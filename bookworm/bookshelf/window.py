# coding: utf-8

import os
import operator
import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from functools import partial
from bookworm import speech
from bookworm.concurrency import threaded_worker
from bookworm.image_io import ImageIO
from bookworm.utils import fuzzy_search
from bookworm.reader import EBookReader
from bookworm.gui.components import AsyncSnakDialog
from bookworm.gui.book_viewer.core_dialogs import DocumentInfoDialog
from bookworm.resources import sounds
from bookworm.paths import app_path, images_path
from bookworm.bookshelf.provider import (
    BookshelfProvider,
    Source,
    MetaSource,
    ItemContainerSource,
    BookshelfAction,
    sources_updated,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class BookshelfNotebookPage(sc.SizedPanel):
    def __init__(self, parent, frame, source):
        super().__init__(parent, -1)
        self.frame = frame
        self.source = source

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
        selected_action_id = self.frame.GetPopupMenuSelectionFromUser(menu, menu_pos)
        if selected_action_id != wx.ID_NONE:
            action = actions[selected_action_id]
            action.func(*args, **kwargs)

    def get_label(self):
        # Translator: label of a reading list or collection entry in the bookshelf tree. It shows the count of documents under that reading list/collection
        return _("{name} ({count})").format(
            name=self.source.name, count=self.source.get_item_count()
        )

    def update_items(self):
        pass


class EmptyBookshelfPage(BookshelfNotebookPage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.Enable(False)


class BookshelfResultsPage(BookshelfNotebookPage):

    ITEM_ACTIVATION_KEYS = {
        wx.WXK_RETURN,
        wx.WXK_NUMPAD_ENTER,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Translators: label of a text box to filter documents in bookshelf
        quick_filter_label = _("Filter documents...")
        wx.StaticText(self, -1, quick_filter_label.rstrip("..."))
        self.quickFilterTextCtrl = wx.TextCtrl(self, -1)
        self.quickFilterTextCtrl.SetHint(quick_filter_label)
        self.quickFilterTextCtrl.SetSizerProps(expand=True)
        # Translators: label of the bookshelf document list. This label is shown when the documents are being loaded from the database
        self.list_label = wx.StaticText(self, -1, _("Loading items"))
        doc_list_style = wx.LC_ICON | wx.LC_SINGLE_SEL
        if self.source.can_rename_items:
            doc_list_style |= wx.LC_EDIT_LABELS
        self.document_list = wx.ListCtrl(self, wx.ID_ANY, style=doc_list_style)
        self.document_list.SetSizerProps(expand=True)
        self.document_list.SetMinSize((2000, 1000))
        self.document_list.Font = (
            self.document_list.Font.MakeLarger().MakeLarger().MakeBold()
        )
        self.quickFilterTextCtrl.MoveAfterInTabOrder(self.document_list)
        self.Layout()
        # Why not use `wx.EVT_LIST_ITEM_ACTIVATED`? because pressing the spacebar is considered
        # activation command. Here we need the spacebar to be handled as a `char` because you can quickly
        # jump between items by typing
        self.document_list.Bind(wx.EVT_KEY_UP, self.onListKeyUP, self.document_list)
        self.document_list.Bind(
            wx.EVT_LEFT_DCLICK,
            lambda e: self.activate_current_item(),
            self.document_list,
        )
        self.document_list.Bind(
            wx.EVT_CHAR, self.onDocumentListChar, self.document_list
        )
        self.document_list.Bind(
            wx.EVT_LIST_END_LABEL_EDIT,
            self.onDocumentListEndLabelEdit,
            self.document_list,
        )
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu, self.document_list)
        self.Bind(wx.EVT_TEXT, self.onQuickFilterTextChanged, self.quickFilterTextCtrl)
        self._all_items = None
        self.items = None
        self.__source_navigation_stack = []

    def set_focused_item(self, idx):
        self.document_list.SetFocus()
        if idx >= self.document_list.GetItemCount():
            return
        self.document_list.EnsureVisible(idx)
        self.document_list.Select(idx)
        self.document_list.SetItemState(
            idx, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED | wx.LIST_STATE_SELECTED
        )

    def update_items(self):
        self.items = None
        if self.IsShown():
            callback = partial(
                self._update_items_future_callback, self.selected_item_index
            )
            threaded_worker.submit(
                self.get_source_items, self.source
            ).add_done_callback(callback)

    def _update_items_future_callback(self, current_selection, future):
        self._get_items_callback(future)
        if future.exception() is None:
            if current_selection < 0:
                sel = 0
            elif current_selection >= (item_count := self.document_list.GetItemCount()):
                sel = item_count - 1
            else:
                sel = current_selection
            if self.selected_item_index != sel:
                self.set_focused_item(sel)

    def add_documents(self):
        if self.items is not None:
            return
        threaded_worker.submit(self.get_source_items, self.source).add_done_callback(
            self._add_documents_callback
        )

    def _add_documents_callback(self, future):
        self._get_items_callback(future)
        if future.exception() is None:
            self.document_list.SetFocus()
            self.set_focused_item(0)
            sounds.navigation.play()

    def create_image_list_from_items(self, items):
        icon_size = (220, 220)
        image_list = wx.ImageList(*icon_size, mask=False)
        generic_file_icon = (
            ImageIO.from_filename(images_path("generic_document.png"))
            .make_thumbnail(*icon_size, exact_fit=True)
            .to_wx_bitmap()
        )
        for (idx, item) in enumerate(items):
            if cover_image := item.cover_image:
                item_icon = cover_image.make_thumbnail(
                    *icon_size, exact_fit=True
                ).to_wx_bitmap()
            else:
                item_icon = generic_file_icon
            wx.CallAfter(image_list.Add, item_icon)
        return image_list

    def get_source_items(self, source):
        items = tuple(source.iter_items())
        return items, self.create_image_list_from_items(items)

    def _get_items_callback(self, future):
        try:
            result = future.result()
        except Exception:
            log.exception(f"Failed to retrieve items for source: {self}", exc_info=True)
            wx.MessageBox(
                # Translators: content of a message shown when the bookshelf fails to load and show documents
                _("Failed to retrieve documents.\nPlease try again."),
                # Translators: title of a message indicating an error
                _("Error"),
                style=wx.ICON_ERROR,
            )
        else:
            items, image_list = result
            self._all_items = items
            self.render_items(items, image_list)

    def render_items(self, items, image_list, set_focus_to_first_item=True):
        self.document_list.ClearAll()
        self.document_list.DeleteAllItems()
        self.__source_navigation_stack.clear()
        self.items = items
        self.document_list.AssignImageList(image_list, wx.IMAGE_LIST_NORMAL)
        for (idx, item) in enumerate(items):
            wx.CallAfter(self.document_list.InsertItem, idx, item.title, idx)
        self.document_list.RefreshItems(0, self.document_list.GetItemCount())
        self.list_label.SetLabel(self.source.name)
        if set_focus_to_first_item:
            self.set_focused_item(0)

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
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("&Open"),
                func=self._do_open_document,
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("Open in &system viewer"),
                func=self._do_open_document_in_system_viewer,
            ),
            BookshelfAction(
                # Translators: label of an item in the context menu of a document in the bookshelf
                _("Edit &title"),
                func=lambda item: self.document_list.EditLabel(
                    self.selected_item_index
                ),
                decider=lambda item: self.source.can_rename_items,
            ),
        ]

    def _do_open_document(self, document_info):
        sounds.navigation.play()
        # Translators: spoken message when activating a document
        speech.announce("Openning document...")
        uri = self.source.resolve_item_uri(document_info)
        EBookReader.open_document_in_a_new_instance(uri)

    def _do_open_document_in_system_viewer(self, document_info):
        uri = self.source.resolve_item_uri(document_info)
        wx.LaunchDefaultApplication(str(uri.path))
        sounds.navigation.play()
        # Translators: spoken message when activating a document
        speech.announce("Openning document...")

    def _do_show_document_info(self, document_info):
        with DocumentInfoDialog(
            parent=self,
            document_info=document_info,
            offer_open_action=True,
            open_in_a_new_instance=True,
        ) as dlg:
            dlg.CenterOnScreen()
            dlg.ShowModal()

    def onQuickFilterTextChanged(self, event):
        self.set_focused_item(0)
        filter_query = event.GetString().strip()
        if not filter_query:
            self.update_items()
        else:
            self.filter_document_list(filter_query)

    def filter_document_list(self, filter_query):
        matching_items = fuzzy_search(
            filter_query, self._all_items, string_converter=operator.attrgetter("title")
        )
        self.document_list.DeleteAllItems()
        self.items = matching_items
        self.render_items(
            matching_items,
            self.create_image_list_from_items(matching_items),
            set_focus_to_first_item=False,
        )
        if not matching_items:
            # Translators: spoken message when no matching documents were found when filtering the document list
            speech.announce(_("No matching documents"))

    def onDocumentListChar(self, event):
        if event.KeyCode in self.ITEM_ACTIVATION_KEYS:
            self.activate_current_item()
            return
        elif event.GetKeyCode() == wx.WXK_ESCAPE:
            return
        elif event.GetKeyCode() == wx.WXK_CONTROL_A:
            self.quickFilterTextCtrl.SetFocus()
            self.quickFilterTextCtrl.SelectAll()
            return
        elif event.GetKeyCode() == wx.WXK_CONTROL_Y:
            self.quickFilterTextCtrl.Redo()
            return
        elif event.GetKeyCode() == wx.WXK_CONTROL_Z:
            self.quickFilterTextCtrl.Undo()
            return
        elif event.KeyCode == 8:
            if not self.quickFilterTextCtrl.IsEmpty():
                self.quickFilterTextCtrl.SetValue(self.quickFilterTextCtrl.Value[:-1])
                self.set_focused_item(0)
            return
        elif (unicode_char := event.GetUnicodeKey()) != wx.WXK_NONE:
            if not event.ControlDown():
                self.quickFilterTextCtrl.AppendText(chr(unicode_char))
                self.set_focused_item(0)
        else:
            event.Skip()

    def onListKeyUP(self, event):
        event.Skip()
        if event.KeyCode == wx.WXK_F2:
            self.document_list.EditLabel(self.selected_item_index)
        elif event.KeyCode == wx.WXK_F5:
            self.update_items()
            self.frame.update_pages_labels()
        elif event.ControlDown() and event.KeyCode == ord("F"):
            self.quickFilterTextCtrl.SetFocus()
        elif event.AltDown() and (event.KeyCode == wx.WXK_LEFT):
            self.pop_folder_navigation_stack()

    def onDocumentListEndLabelEdit(self, event):
        new_title = event.GetLabel().strip()
        if new_title:
            self.source.change_item_title(self.selected_item, new_title)

    def pop_folder_navigation_stack(self):
        try:
            prev_source = self.__source_navigation_stack.pop()
        except IndexError:
            return
        AsyncSnakDialog(
            # Translators: message shown when loading documents in the bookshelf
            message=_("Retrieving items..."),
            task=partial(self.get_source_items, prev_source),
            done_callback=self._get_items_callback,
            parent=self.frame,
        )

    def activate_current_item(self):
        if (item := self.selected_item) is None:
            return
        if isinstance(item, ItemContainerSource):
            AsyncSnakDialog(
                # Translators: message shown when loading documents in the bookshelf
                message=_("Retrieving items..."),
                task=partial(self.get_source_items, item),
                done_callback=self._navigate_to_folder,
                parent=self.frame,
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
                *item_actions,
                BookshelfAction(
                    # Translators: label of an item in the context menu of a document in the bookshelf
                    _("Document &info..."),
                    func=self._do_show_document_info,
                ),
            ]
        rect = self.document_list.GetItemRect(self.selected_item_index)
        self.popup_actions_menu(actions, wx.Point(rect.Right, rect.Bottom), item)


class BookshelfWindow(sc.SizedFrame):
    def __init__(self, parent):
        super().__init__(parent)
        icon_file = app_path("bookshelf.ico")
        icon = wx.Icon()
        icon.LoadFile(os.fspath(icon_file))
        self.SetIcon(icon)
        self.providers = BookshelfProvider.get_providers()
        self.menubar = wx.MenuBar()
        self.SetMenuBar(self.menubar)
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
        # Translators: label of the combo box showing a list of bookshelf providers.
        # Currently, only the Local Bookshelf provider is implemented. In the future, other providers may be added, such as Bookshare and Pocket.
        wx.StaticText(lhs_panel, -1, _("Provider"))
        self.provider_choice = wx.Choice(
            lhs_panel,
            -1,
            choices=[prov.display_name for prov in self.providers],
        )
        # Translators: label of the bookshelf tree that shows reading lists and collections and other categories
        wx.StaticText(lhs_panel, -1, _("Categories"))
        self.tree_tabs = wx.Treebook(lhs_panel, -1)
        self.tree_tabs.SetSizerProps(expand=True)
        tree_ctrl = self.tree_tabs.GetTreeCtrl()
        tree_ctrl.SetMinSize((200, 1000))
        # Translators: label of the bookshelf tree that shows reading lists and collections and other categories
        tree_ctrl.SetLabel(_("Categories"))
        self.Bind(wx.EVT_CHOICE, self.onProviderChoiceChange, self.provider_choice)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged, self.tree_tabs)
        tree_ctrl.Bind(wx.EVT_KEY_UP, self.onTreeKeyUp, tree_ctrl)
        tree_ctrl.Bind(wx.EVT_TREE_ITEM_MENU, self.onTreeContextMenu)
        self.provider_choice.SetSelection(0)
        self.setup_provider()

    @property
    def provider(self):
        return self.providers[self.provider_choice.GetSelection()]

    def _handle_source_updated(self, sender, update_sources=False, update_items=False):
        if update_sources:
            self.setup_provider()
            self.tree_tabs.GetTreeCtrl().SetFocus()
            self.tree_tabs.Refresh()
        if update_items:
            for page_idx in range(0, self.tree_tabs.GetPageCount()):
                try:
                    page = self.tree_tabs.GetPage(page_idx)
                except wx.wxAssertionError:
                    continue
                if not page.source.is_valid():
                    self.tree_tabs.DeletePage(page_idx)
                    continue
                page.update_items()
        self.update_pages_labels()

    def update_pages_labels(self):
        for page_idx in range(0, self.tree_tabs.GetPageCount()):
            page = self.tree_tabs.GetPage(page_idx)
            self.tree_tabs.SetPageText(page_idx, page.get_label())

    def setup_provider(self):
        self.SetTitle(
            # Translators: title of Bookshelf window
            _("Bookworm Bookshelf: {name}").format(name=self.provider.display_name)
        )
        self.tree_tabs.DeleteAllPages()
        self.add_sources(self.provider.get_sources(), self.tree_tabs)
        for (menu_idx, (mb_menu, __)) in enumerate(self.menubar.GetMenus()):
            for menu_item in mb_menu.GetMenuItems():
                self.Unbind(wx.EVT_MENU, id=menu_item.GetId())
            self.menubar.Remove(menu_idx)
            mb_menu.Destroy()
        menu_actions = {
            wx.NewIdRef(): action
            for action in self.provider.get_provider_actions()
            if action.decider(self.provider)
        }
        menu = wx.Menu()
        for (item_id, action) in menu_actions.items():
            menu.Append(item_id, action.display)
            self.Bind(
                wx.EVT_MENU,
                partial(self._on_provider_menu_item_clicked, action.func),
                id=item_id,
            )
        menu.AppendSeparator()
        # Translators: label of a menu item to exit the application
        menu.Append(wx.ID_CLOSE, _("&Exit"))
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), id=wx.ID_CLOSE)
        # Translators: lable of the file menu in the menu bar
        self.menubar.Append(menu, _("&File"))
        sources_updated.disconnect(self._handle_source_updated)
        sources_updated.connect(self._handle_source_updated, sender=self.provider)
        self.tree_tabs.SetFocus()

    def add_sources(self, sources, tree_tabs, as_subpage=False):
        for source in sources:
            if not source.is_valid():
                continue
            if isinstance(source, MetaSource):
                page = EmptyBookshelfPage(tree_tabs, self, source)
                tree_tabs.AddPage(page, page.get_label())
                self.add_sources(source, tree_tabs, as_subpage=True)
            else:
                func = tree_tabs.AddSubPage if as_subpage else tree_tabs.AddPage
                page = BookshelfResultsPage(tree_tabs, self, source)
                func(page, page.get_label())

    def onProviderChoiceChange(self, event):
        self.setup_provider()

    def OnPageChanged(self, event):
        page_idx = self.tree_tabs.GetSelection()
        selected_page = self.tree_tabs.GetPage(page_idx)
        if isinstance(selected_page, BookshelfResultsPage):
            selected_page.add_documents()

    def onTreeKeyUp(self, event):
        event.Skip()
        if event.KeyCode == wx.WXK_F5:
            self.setup_provider()

    def onTreeContextMenu(self, event):
        page_idx = self.tree_tabs.GetSelection()
        if page_idx == wx.NOT_FOUND:
            return
        selected_page = self.tree_tabs.GetPage(page_idx)
        source = selected_page.source
        actions = (
            action for action in source.get_source_actions() if action.decider(source)
        )
        selected_page.popup_actions_menu(actions, event.GetPoint(), source=source)

    def _on_provider_menu_item_clicked(self, action_func, event):
        action_func(self.provider)


def run_bookshelf_standalone():
    from bookworm.bootstrap import BookwormApp, setupSubsystems, log_diagnostic_info

    app = BookwormApp()

    log_diagnostic_info()
    setupSubsystems()

    frame = BookshelfWindow(None)
    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()
