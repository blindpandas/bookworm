# coding: utf-8

import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from functools import partial
from bookworm.concurrency import threaded_worker
from bookworm.gui.components import ImmutableObjectListView
from bookworm.gui.book_viewer.core_dialogs import DocumentInfoDialog
from bookworm.resources import sounds
from bookworm.bookshelf.provider import BookshelfProvider, Source, ContainerSource
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
            menu.Append(item_id, action.display)
        selected_action_id = self.frame.GetPopupMenuSelectionFromUser(
            menu,
            menu_pos
        )
        action = actions[selected_action_id]
        action.func(*args, **kwargs)


class EmptyBookshelfPage(BookshelfNotebookPage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Enable(False)



class BookshelfResultsPage(BookshelfNotebookPage):

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
        self.items = None
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.onItemActivated, self.document_list)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu, self.document_list)

    def add_documents(self):
        if self.items is not None:
            return
        threaded_worker.submit(
            self._process_items_for_display,
        ).add_done_callback(self.render_items)

    def _process_items_for_display(self):
        items = tuple(self.source)
        icon_size = (220, 220)
        image_list = wx.ImageList(*icon_size, mask=False)
        empty_bitmap = wx.Bitmap(wx.Size(*icon_size))
        for (idx, doc_info) in enumerate(items):
            if (cover_image := doc_info.cover_image):
                item_icon = cover_image.make_thumbnail(*icon_size, exact_fit=True).to_wx_bitmap()
            else:
                item_icon = empty_bitmap
            wx.CallAfter(image_list.Add, item_icon)
        return items, image_list

    def render_items(self, future):
        try:
            result = future.result()
        except Exception:
            log.exception(f"Failed to retrieve items for source: {self}", exc_info=True)
            return
        items, image_list = result
        self.items = items
        self.document_list.AssignImageList(image_list, wx.IMAGE_LIST_NORMAL)
        for (idx, item) in enumerate(items):
            wx.CallAfter(self.document_list.InsertItem, idx, item.title, idx)
        self.document_list.RefreshItems(0, self.document_list.GetItemCount())
        #self.document_list.Layout()
        self.list_label.SetLabel(_("Documents"))
        sounds.navigation.play()
        if self.document_list.HasFocus():
            ImmutableObjectListView.set_focused_item(self.document_list, 0)


    @property
    def selected_item(self):
        if (idx := self.document_list.GetFocusedItem()) == wx.NOT_FOUND:
            return
        return self.items[idx]

    @property
    def selected_item_index(self):
        return self.document_list.GetFocusedItem()

    def onItemActivated(self, event):
        if (doc_info := self.selected_item) is not None:
            with DocumentInfoDialog(parent=self, document_info=doc_info, offer_open_action=True, open_in_a_new_instance=True) as dlg:
                dlg.CenterOnScreen()
                dlg.ShowModal()

    def onContextMenu(self, event):
        if (doc_info := self.selected_item) is None:
            return
        actions = (
            action
            for action in self.source.get_item_actions(doc_info)
            if action.decider(doc_info)
        )
        rect = self.document_list.GetItemRect(self.selected_item_index)
        self.popup_actions_menu(
            actions,
            wx.Point(rect.Right, rect.Bottom),
            doc_info,
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

    def setup_provider(self):
        self.add_sources(
            self.provider.get_sources(),
            self.tree_tabs
        )

    def add_sources(self, sources, tree_tabs):
        for source in sources:
            if isinstance(source, ContainerSource):
                tree_tabs.AddPage(
                    EmptyBookshelfPage(tree_tabs, self, source),
                    source.name
                )
                self.add_sources(source, tree_tabs)
            else:
                tree_tabs.AddSubPage(
                BookshelfResultsPage(tree_tabs, self, source),
                source.name
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
        selected_page.popup_actions_menu(
            selected_page.source.get_source_actions(),
            event.GetPoint(),
            source=selected_page.source,
        )


def run_bookshelf_standalone():
    from bookworm.bootstrap import BookwormApp, setupSubsystems, log_diagnostic_info

    app = BookwormApp()
    frame = BookshelfWindow(None, _("Bookworm Bookshelf"))
    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()
