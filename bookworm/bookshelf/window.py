# coding: utf-8

import winsound
import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from functools import partial
from bookworm import speech
from bookworm.concurrency import threaded_worker
from bookworm.image_io import ImageIO
from bookworm.reader import EBookReader
from bookworm.gui.components import DialogListCtrl, AsyncSnakDialog
from bookworm.gui.book_viewer.core_dialogs import DocumentInfoDialog
from bookworm.resources import sounds
from bookworm.paths import images_path
from bookworm.bookshelf.provider import (
    BookshelfProvider,
    Source,
    MetaSource,
    ItemContainerSource,
    BookshelfAction,
    sources_updated,
    items_updated,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookshelfNotebookPage(sc.SizedPanel):

    def __init__(self, parent, frame, source):
        super().__init__(parent, -1)
        self.frame = frame
        self.source =source

    def popup_actions_menu(self, actions, menu_pos, *args, **kwargs):
        actions = {wx.NewIdRef(): action for action in actions}
        if not actions:
            return
        menu = wx.Menu()
        for (item_id, action) in actions.items():
            if action is None:
                menu.AppendSeparator()
                continue
            menu.Append(item_id, action.display)
        selected_action_id = self.frame.GetPopupMenuSelectionFromUser(
            menu,
            menu_pos
        )
        if selected_action_id != wx.ID_NONE:
            action = actions[selected_action_id]
            action.func(*args, **kwargs)


class EmptyBookshelfPage(BookshelfNotebookPage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Enable(False)



class BookshelfResultsPage(BookshelfNotebookPage):

    ITEM_ACTIVATION_KEYS = {wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER,}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_label = wx.StaticText(self, -1, _("Loading items"))
        self.document_list = wx.ListCtrl(
            self,
            wx.ID_ANY,
            style=wx.LC_ICON | wx.LC_SINGLE_SEL
        )
        self.SetSizerType('Grid')
        self.document_list.SetSizerProps(expand=True)
        self.document_list.SetMinSize((2000, 1000))
        self.document_list.Font = self.document_list.Font.MakeLarger().MakeLarger().MakeBold()
        self.Layout()
        # Why not use `wx.EVT_LIST_ITEM_ACTIVATED`? because pressing the spacebar is considered
        # activation command. Here we need the spacebar to be handled as a `char` because you can quickly
        # jump between items by typing
        self.document_list.Bind(wx.EVT_KEY_UP, self.onListKeyUP, self.document_list)
        self.document_list.Bind(wx.EVT_LEFT_DCLICK, lambda e: self.activate_current_item(), self.document_list)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu, self.document_list)
        items_updated.connect(
            self._on_items_updated,
            sender=self.source,
        )
        self.items = None
        self.__source_navigation_stack = []

    def _on_items_updated(self, sender):
        winsound.Beep(1000, 1000)
        self.items = None
        self.add_documents()

    def add_documents(self):
        if self.items is not None:
            return
        threaded_worker.submit(
            self.get_source_items,
            self.source
        ).add_done_callback(self._get_items_callback)

    def get_source_items(self, source):
        items = list(source)
        icon_size = (220, 220)
        image_list = wx.ImageList(*icon_size, mask=False)
        generic_file_icon = ImageIO.from_filename(images_path("generic_document.png")).make_thumbnail(*icon_size, exact_fit=True).to_wx_bitmap()
        for (idx, item) in enumerate(items):
            if (cover_image := item.cover_image):
                item_icon = cover_image.make_thumbnail(*icon_size, exact_fit=True).to_wx_bitmap()
            else:
                item_icon = generic_file_icon
            wx.CallAfter(image_list.Add, item_icon)
        return items, image_list

    def _get_items_callback(self, future):
        try:
            result = future.result()
        except Exception:
            log.exception(f"Failed to retrieve items for source: {self}", exc_info=True)
            return
        items, image_list = result
        self.render_items(items, image_list)

    def render_items(self, items, image_list):
        self.document_list.ClearAll()
        self.document_list.SetFocus()
        self.items = items
        self.document_list.AssignImageList(image_list, wx.IMAGE_LIST_NORMAL)
        for (idx, item) in enumerate(items):
            wx.CallAfter(self.document_list.InsertItem, idx, item.title, idx)
        self.document_list.RefreshItems(0, self.document_list.GetItemCount())
        self.list_label.SetLabel(_("Documents"))
        sounds.navigation.play()
        DialogListCtrl.set_focused_item(self.document_list, 0)

    @property
    def selected_item(self):
        if (idx := self.document_list.GetFocusedItem()) == wx.NOT_FOUND:
            return
        return self.items[idx]

    @property
    def selected_item_index(self):
        return self.document_list.GetFocusedItem()

    def _navigate_to_folder(self, future):
        if future.exception() is None:
            self.__source_navigation_stack.append(self.source)
        return self._get_items_callback(future)

    def get_default_item_actions(self, item):
        return [
            BookshelfAction(
                _("Open"),
                func=self._do_open_document, 
            ),
            BookshelfAction(
                _("Document info..."),
                func=self._do_show_document_info 
            ),
        ]

    def _do_open_document(self, document_info):
        speech.announce("Openning...")
        sounds.navigation.play()
        EBookReader.open_document_in_a_new_instance(document_info.uri)

    def _do_show_document_info(self, document_info):
        with DocumentInfoDialog(parent=self, document_info=document_info, offer_open_action=True, open_in_a_new_instance=True) as dlg:
            dlg.CenterOnScreen()
            dlg.ShowModal()

    def onListKeyUP(self, event):
        event.Skip()
        if event.ControlDown() and event.KeyCode in self.ITEM_ACTIVATION_KEYS and self.document_list.HasFocus():
            self.activate_current_item()
        elif event.KeyCode == wx.WXK_BACK:
            self.pop_folder_navigation_stack()
        elif event.AltDown() and (event.KeyCode == wx.WXK_LEFT):
            self.pop_folder_navigation_stack()

    def pop_folder_navigation_stack(self):
        try:
            prev_source = self.__source_navigation_stack.pop()
        except IndexError:
            wx.Bell()
            return
        AsyncSnakDialog(
            message=_("Retrieving items..."),
            task=partial(self.get_source_items, prev_source),
            done_callback=self._get_items_callback,
            parent=self.frame
        )

    def activate_current_item(self):
        if (item := self.selected_item) is None:
            return
        if isinstance(item, ItemContainerSource):
            AsyncSnakDialog(
                message=_("Retrieving items..."),
                task=partial(self.get_source_items, item),
                done_callback=self._navigate_to_folder,
                parent=self.frame
            )
        else:
            self._do_open_document(item)

    def onContextMenu(self, event):
        if (item := self.selected_item) is None:
            return
        if isinstance(item, ItemContainerSource):
            actions = item.get_source_actions()
        else:
            item_actions = [
                action
                for action in self.source.get_item_actions(item)
                if action.decider(item)
            ]
            actions = [
                *self.get_default_item_actions(item),
                None,
                *item_actions
            ]
        rect = self.document_list.GetItemRect(self.selected_item_index)
        self.popup_actions_menu(
            actions,
            wx.Point(rect.Right, rect.Bottom),
            item
        )


class BookshelfWindow(sc.SizedFrame):
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, title=title, **kwargs)
        self.providers = BookshelfProvider.get_providers()
        self.make_controls()
        self.CenterOnScreen()
        self.Maximize()

    def make_controls(self):
        panel = self.GetContentsPane()
        panel.SetSizerType("horizontal")
        panel.SetSizerProps(expand=True)
        lhs_panel = sc.SizedPanel(panel)
        lhs_panel.SetSizerType("vertical")
        lhs_panel.SetSizerProps(expand=True)
        wx.StaticText(lhs_panel, -1, _("Provider"))
        self.provider_choice = wx.Choice(
            lhs_panel,
            -1,
            choices=[prov.display_name for prov in self.providers],
        )
        wx.StaticText(lhs_panel, -1, _("Categories"))
        self.tree_tabs = wx.Treebook(lhs_panel, -1)
        self.tree_tabs.SetSizerProps(expand=True)
        tree_ctrl = self.tree_tabs.GetTreeCtrl()
        tree_ctrl.SetMinSize((200, 1000))
        tree_ctrl.SetLabel(_("Categories"))
        self.Bind(wx.EVT_CHOICE, self.onProviderChoiceChange, self.provider_choice)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged, self.tree_tabs)
        tree_ctrl.Bind(wx.EVT_TREE_ITEM_MENU, self.onTreeContextMenu)
        self.provider_choice.SetSelection(0)
        self.setup_provider()

    @property
    def provider(self):
        return self.providers[self.provider_choice.GetSelection()]

    def _handle_source_updated(self, sender):
        self.setup_provider()
        self.tree_tabs.GetTreeCtrl().SetFocus()
        self.tree_tabs.Refresh()

    def setup_provider(self):
        self.tree_tabs.DeleteAllPages()
        self.add_sources(
            self.provider.get_sources(),
            self.tree_tabs
        )
        sources_updated.disconnect(self._handle_source_updated)
        sources_updated.connect(self._handle_source_updated, sender=self.provider)

    def add_sources(self, sources, tree_tabs, as_subpage=False):
        for source in sources:
            if type(source) is MetaSource:
                tree_tabs.AddPage(
                    EmptyBookshelfPage(tree_tabs, self, source),
                    _("{name} ({count})").format(name=source.name, count=source.get_item_count())
                )
                self.add_sources(source, tree_tabs, as_subpage=True)
            else:
                func = tree_tabs.AddSubPage if as_subpage else tree_tabs.AddPage
                func(
                    BookshelfResultsPage(tree_tabs, self, source),
                    _("{name} ({count})").format(name=source.name, count=source.get_item_count())
                )

    def onProviderChoiceChange(self, event):
        self.setup_provider()

    def OnPageChanged(self, event):
        page_idx = self.tree_tabs.GetSelection()
        selected_page = self.tree_tabs.GetPage(page_idx)
        if isinstance(selected_page, BookshelfResultsPage):
            selected_page.add_documents()

    def onTreeContextMenu(self, event):
        page_idx = self.tree_tabs.GetSelection()
        if page_idx == wx.NOT_FOUND:
            return
        selected_page = self.tree_tabs.GetPage(page_idx)
        source = selected_page.source
        actions = (
            action
            for action in source.get_source_actions()
            if action.decider(source)
        )
        selected_page.popup_actions_menu(
            actions,
            event.GetPoint(),
            source=source
        )


def run_bookshelf_standalone():
    from bookworm.bootstrap import BookwormApp, setupSubsystems, log_diagnostic_info

    app = BookwormApp()

    log_diagnostic_info()
    setupSubsystems()

    frame = BookshelfWindow(None, _("Bookworm Bookshelf"))
    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()
