# coding: utf-8

import threading
import webbrowser
from functools import partial, lru_cache

import wx
import wx.lib.sized_controls as sc
from bidict import bidict
from mediawiki import MediaWiki
from mediawiki.exceptions import DisambiguationError, PageError

from bookworm import app
from bookworm.paths import resources_path
from bookworm.i18n import LocaleInfo
from bookworm.gui.components import AsyncSnakDialog, SimpleDialog
from bookworm.logger import logger
from bookworm.resources import sounds
from bookworm.service import BookwormService

log = logger.getChild(__name__)


class NoMatches(Exception):
    """Raised when no page matches the given term."""


class MultipleMatches(Exception):
    """Raised when multiple pages were found for the given term."""

    def __init__(self, options, language):
        self.options = options
        self.language = language


@lru_cache
def get_wikipedia_languages():
    with open(resources_path("Wikipedia.languages.txt"), "r") as file:
        return [line.strip() for line in file]


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
            _("Get a quick definition from Wikipedia"),
        )
        self.view.Bind(
            wx.EVT_MENU, self.onQuickWikiSearch, id=self.wiki_quick_search_id
        )

    def get_contextmenu_items(self):
        rv = ()
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            rv = [
                (
                    2,
                    _("Define using Wikipedia"),
                    _("Define the selected text using Wikipedia"),
                    self.wiki_quick_search_id,
                )
            ]
        return rv

    def get_keyboard_shortcuts(self):
        return {self.wiki_quick_search_id: "Ctrl+Shift+W"}

    def onQuickWikiSearch(self, event):
        if selected_text := self.view.contentTextCtrl.GetStringSelection().strip():
            term = selected_text
        else:
            term = ""
        language = (
            self.view.reader.document.language
            if self.view.reader.ready
            else app.current_language
        )
        with SearchWikipediaDialog(term, language) as wikiDlg:
            if (retval := wikiDlg.ShowModal()) is not None:
                term, language = retval
                self.init_wikipedia_search(term, language)

    def init_wikipedia_search(self, term, language, sure_exists=False):
        AsyncSnakDialog(
            task=partial(
                self.define_term_using_wikipedia, term, language, sure_exists=sure_exists
            ),
            done_callback=self.view_wikipedia_definition,
            dismiss_callback=lambda: self._cancel_query.set() or True,
            message=_("Retrieving information, please wait..."),
            parent=self.view,
        )

    def define_term_using_wikipedia(self, term: str, language, sure_exists=False) -> str:
        wiki = MediaWiki(lang=language)
        try:
            page = wiki.page(title=term, auto_suggest=True, preload=True)
        except DisambiguationError as e:
            raise MultipleMatches(e.options, language)
        except PageError:
            search_results = [
                title
                for (title, __, ___) in wiki.opensearch(term)
            ]
            if search_results:
                raise MultipleMatches(search_results, language)
            else:
                 raise NoMatches(f"No results for the term `{term}`")
        else:
            return page.title, page.summary, page.url

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
                _(
                    "Could not connect to Wikipedia at the moment.\Please make sure that you're connected to the internet or try again later."
                ),
                icon=wx.ICON_WARNING,
            )
        except NoMatches:
            log.exception("Failed to find a page for the given term in Wikipedia", exc_info=True)
            self.view.notify_user(
                # Translators: title of a message box
                _("Page not found"),
                # Translators: content of a message box
                _("Could not find a Wikipedia page for the given term.."),
                icon=wx.ICON_ERROR,
            )
        except MultipleMatches as e:
            dlg = wx.SingleChoiceDialog(
                self.view,
                _("Matches"),
                _("Multiple Matches Found"),
                e.options,
                wx.CHOICEDLG_STYLE,
            )
            if dlg.ShowModal() == wx.ID_OK:
                term = dlg.GetStringSelection()
                return self.init_wikipedia_search(term, language=e.language, sure_exists=True)
            else:
                return
        except:
            log.exception("Failed to get definition from Wikipedia", exc_info=True)
            self.view.notify_user(
                _("Error"),
                _("Failed to get term definition from Wikipedia."),
                icon=wx.ICON_WARNING,
            )
        else:
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
            title=_("{term} — Wikipedia").format(term=term),
            parent=wx.GetApp().mainFrame,
        )

    def addControls(self, parent):
        # Translators: label of a read only edit control showing Wikipedia article summary
        wx.StaticText(parent, -1, _("Summary"))
        contentText = wx.TextCtrl(
            parent,
            size=(500, 200),
            style=wx.TE_READONLY | wx.TE_MULTILINE,
        )
        contentText.SetSizerProps(expand=True)
        contentText.SetValue(self.definition)
        btnPanel = sc.SizedPanel(parent)
        btnPanel.SetSizerType("horizontal")
        btnPanel.SetSizerProps(halign="center", expand=True)
        openInBookwormBtn = wx.Button(btnPanel, -1, _("Open in &Bookworm"))
        openInBrowserBtn = wx.Button(btnPanel, wx.ID_OPEN, _("&Open in Browser"))
        self.Bind(
            wx.EVT_BUTTON, lambda e: webbrowser.open(self.page_url), openInBrowserBtn
        )
        self.Bind(wx.EVT_BUTTON, self.onOpenInBookworm, openInBookwormBtn)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of a button to close a dialog
        btnsizer.AddButton(wx.Button(self, wx.ID_CANCEL, _("&Close")))
        btnsizer.Realize()
        return btnsizer

    def onOpenInBookworm(self, event):
        self.Close()
        wx.GetApp().service_handler.get_service("url_open").open_url_in_bookworm(
            self.page_url
        )



class SearchWikipediaDialog(SimpleDialog):

    def __init__(self, term="", chosen_language=None):
        self.term = term
        self.chosen_language = chosen_language
        self.supported_languages = bidict({
            lang: LocaleInfo(lang).description
            for lang in get_wikipedia_languages()
        })
        self.supported_languages_display = list(sorted(self.supported_languages.values()))
        super().__init__(
            # Translators: the title of a dialog to search for a term in Wikipedia
            title=_("Wikipedia Quick Search"),
            parent=wx.GetApp().mainFrame,
        )

    def addControls(self, parent):
        # Translators: label of an edit control in the search Wikipedia dialog
        wx.StaticText(parent, -1, _("Enter term"))
        self.termEntry = wx.TextCtrl(parent)
        self.termEntry.SetSizerProps(expand=True)
        if self.term:
            self.termEntry.SetValue(self.term)
        # Translators: label of a combobox  that shows a list of languages to search in Wikipedia 
        wx.StaticText(parent, -1, _("Choose Wikipedia language"))
        self.languageChoice = wx.Choice(parent, choices=self.supported_languages_display)
        if self.chosen_language is not None:
            self.languageChoice.SetStringSelection(self.chosen_language.parent.description)
        if  self.languageChoice.GetSelection() == wx.NOT_FOUND:
            self.languageChoice.SetStringSelection(LocaleInfo("en").description)

    def ShowModal(self):
        if super().ShowModal() == wx.ID_OK and (termValue := self.termEntry.GetValue().strip()):
            return (
                termValue,
                self.supported_languages.inverse[self.languageChoice.GetStringSelection()]
            )