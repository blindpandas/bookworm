# coding: utf-8

import threading
import wx
import webbrowser
import wikipedia
from functools import partial
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

    def process_menubar(self, menubar):
        self.defineOnWikiId = wx.NewIdRef()
        self.view.Bind(wx.EVT_MENU, self.onDefineFromWikipedia, id=self.defineOnWikiId)

    def get_contextmenu_items(self):
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            return [
                (
                    2,
                    _("Define using Wikipedia"),
                    _("Define the selected text using Wikipedia"),
                    self.defineOnWikiId
                )
            ]

    def onDefineFromWikipedia(self, event):
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            AsyncSnakDialog(
                task=partial(self.define_term_using_wikipedia, selected_text),
                done_callback=self.view_wikipedia_definition,
                dismiss_callback=lambda: self._cancel_query.set() or True,
                message=_("Connecting to Wikipedia, please wait..."),
                parent=self.view
            )

    def define_term_using_wikipedia(self, term: str) -> str:
        language = self.view.reader.document.language
        wikipedia.set_lang(language)
        if (suggested := wikipedia.suggest(term)) is not None:
            return wikipedia.page(suggest)
        else:
            search_results = wikipedia.search(term)
            return wikipedia.page(search_results[0])

    def view_wikipedia_definition(self, future):
        if self._cancel_query.is_set():
            self._cancel_query.clear()
            return
        try:
            page = future.result()
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
        sounds.navigation.play()
        ViewWikipediaDefinition(page.title, page.summary.strip(), page.url).ShowModal()

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
        wx.Button(parent, wx.ID_OPEN, _("Open in Browser"))
        self.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open(self.page_url), id=wx.ID_OPEN)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close a dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer
