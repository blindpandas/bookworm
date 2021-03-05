# coding: utf-8

import threading
import wx
import webbrowser
import wikipedia
from functools import partial
from bookworm import app
from bookworm.gui.components import AsyncSnakDialog, SimpleDialog
from bookworm.base_service import BookwormService
from bookworm.resources import sounds
from bookworm.logger import logger

log = logger.getChild(__name__)


class WikipediaService(BookwormService):
    name = "wikipedia"
    config_spec = {}
    has_gui = True

    def __post_init__(self):
        self._cancel_query = threading.Event()
        self.wiki_quick_search_id = wx.NewIdRef()

    def process_menubar(self, menubar):
        webservices_menu = (
            wx.GetApp().service_handler.get_service("webservices").web_sservices_menu
        )
        webservices_menu.Append(
            self.wiki_quick_search_id,
            _("&Wikipedia quick search"),
            _("Get a quick definition from Wikipedia")
        )
        self.view.Bind(wx.EVT_MENU, self.onQuickWikiSearch, id=self.wiki_quick_search_id)

    def get_contextmenu_items(self):
        rv = ()
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            rv =  [
                (
                    2,
                    _("Define using Wikipedia"),
                    _("Define the selected text using Wikipedia"),
                    self.wiki_quick_search_id
                )
            ]
        return rv

    def get_keyboard_shortcuts(self):
        return {
            self.wiki_quick_search_id: "Ctrl+Shift+W"
        }

    def onQuickWikiSearch(self, event):
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            self.init_wikipedia_search(selected_text)
        else:
            entered_term = self.view.get_text_from_user(
                title=_("Wikipedia Quick Search"),
                label=_("Enter term"),
            )
            if entered_term is not None:
                self.init_wikipedia_search(entered_term)

    def init_wikipedia_search(self, term, sure_exists=False):
        AsyncSnakDialog(
            task=partial(self.define_term_using_wikipedia, term, sure_exists=sure_exists),
            done_callback=self.view_wikipedia_definition,
            dismiss_callback=lambda: self._cancel_query.set() or True,
            message=_("Retrieving info from Wikipedia, please wait..."),
            parent=self.view
        )

    def define_term_using_wikipedia(self, term: str, sure_exists=False) -> str:
        if self.view.reader.ready:
            language = self.view.reader.document.language
        else:
            language = app.current_language.language
        wikipedia.set_lang(language)
        page = None
        if sure_exists:
            page = wikipedia.page(term)
        elif (suggested := wikipedia.suggest(term)) is not None:
            page = wikipedia.page(suggested)
        if page is not None:
            return (page.title, page.summary.strip(), page.url)
        else:
            return list(wikipedia.search(term))

    def view_wikipedia_definition(self, future):
        if self._cancel_query.is_set():
            self._cancel_query.clear()
            return
        try:
            result = future.result()
        except ConnectionError:
            log.debug("Failed to connect to wikipedia", exc_info=True)
            self.view.notify_user(
                _("Connection Error"),
                _("Could not connect to Wikipedia at the moment.\Please make sure that you're connected to the internet or try again later."),
                icon=wx.ICON_ERROR
            )
            return
        except:
            log.exception("Failed to get definition from Wikipedia", exc_info=True)
            self.view.notify_user(
                _("Error"),
                _("Could not get the definition from Wikipedia."),
                icon=wx.ICON_ERROR
            )
            return
        if type(result) is list:
            dlg = wx.SingleChoiceDialog(
                self.view,
                _("Matches"),
                _("Multiple Matches Found"),
                result,
                wx.CHOICEDLG_STYLE
            )
            if dlg.ShowModal() == wx.ID_OK:
                term = dlg.GetStringSelection()
                return self.init_wikipedia_search(term, sure_exists=True)
            else:
                wx.Bell()
                return
        sounds.navigation.play()
        title, summary, url = result
        ViewWikipediaDefinition(title, summary, url).ShowModal()

class ViewWikipediaDefinition(SimpleDialog):
    """A helper class to view the Wikipedia results."""

    def __init__(self, term, definition, page_url):
        self.term = term
        self.definition = definition
        self.page_url = page_url
        super().__init__(
            title=_("{term} - Wikipedia").format(term=term),
            parent=wx.GetApp().mainFrame,
        )

    def addControls(self, parent):
        # Translators: label of an edit control in the dialog
        # of viewing or editing a comment/highlight
        wx.StaticText(parent, -1, _("Definition"))
        contentText = wx.TextCtrl(
            parent,
            size=(500, 200),
            style=wx.TE_READONLY | wx.TE_MULTILINE,
        )
        contentText.SetSizerProps(expand=True)
        contentText.SetValue(self.definition)
        openBtn = wx.Button(parent, wx.ID_OPEN, _("Open in Browser"))
        openBtn.SetSizerProps(halign="center")
        self.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open(self.page_url), id=wx.ID_OPEN)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close a dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer
