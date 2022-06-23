# coding: utf-8

import sys
import wx
import wx.lib.sized_controls as sc
from enum import IntEnum, auto
from dataclasses import dataclass
from wx.adv import CommandLinkButton
from bookworm import app
from bookworm import config
from bookworm.paths import app_path
from bookworm.utils import restart_application
from bookworm.i18n import get_available_locales, set_locale
from bookworm.signals import app_started, config_updated
from bookworm.runtime import IS_RUNNING_PORTABLE
from bookworm.resources import app_icons
from bookworm.platform_services.shell import (
    shell_integrate,
    shell_disintegrate,
    get_ext_info,
)
from bookworm.logger import logger
from .components import SimpleDialog, EnhancedSpinCtrl


log = logger.getChild(__name__)


class ReconciliationStrategies(IntEnum):
    load = auto()
    save = auto()


class FileAssociationDialog(SimpleDialog):
    """Associate supported file types."""

    def __init__(self, parent, standalone=False):
        # Translators: the title of the file associations dialog
        super().__init__(parent, title=_("Bookworm File Associations"))
        self.standalone = standalone
        icon_file = app_path(f"{app.name}.ico")
        if icon_file.exists():
            self.SetIcon(wx.Icon(str(icon_file)))

    def addControls(self, parent):
        self.ext_info = sorted(get_ext_info().items())
        # Translators: instructions shown to the user in a dialog to set up file association.
        wx.StaticText(
            parent,
            -1,
            _(
                "This dialog will help you to setup file associations.\n"
                "Associating files with Bookworm means that when you click on a file in windows explorer, it will be opened in Bookworm by default "
            ),
        )
        masterPanel = sc.SizedPanel(parent, -1)
        masterPanel.SetSizerType("horizontal")
        panel1 = sc.SizedPanel(masterPanel, -1)
        panel2 = sc.SizedPanel(masterPanel, -1)
        assoc_btn = CommandLinkButton(
            panel1,
            -1,
            # Translators: the main label of a button
            _("Associate all"),
            # Translators: the note of a button
            _("Use Bookworm to open all supported document formats"),
        )
        half = len(self.ext_info) / 2
        buttonPanel = panel1
        for i, (ext, metadata) in enumerate(self.ext_info):
            if i >= half:
                buttonPanel = panel2
            # Translators: the main label of a button
            mlbl = _("Associate files of type {format}").format(format=metadata[1])
            # Translators: the note of a button
            nlbl = _(
                "Associate files with {ext} extension so they always open in Bookworm"
            ).format(ext=ext)
            btn = CommandLinkButton(buttonPanel, -1, mlbl, nlbl)
            self.Bind(
                wx.EVT_BUTTON,
                lambda e, args=(ext, metadata[1]): self.onFileAssoc(*args),
                btn,
            )
        dissoc_btn = CommandLinkButton(
            panel2,
            -1,
            # Translators: the main label of a button
            _("Dissociate all supported file types"),
            # Translators: the note of a button
            _("Remove previously associated file types"),
        )
        self.Bind(wx.EVT_BUTTON, lambda e: self.onBatchAssoc(assoc=True), assoc_btn)
        self.Bind(wx.EVT_BUTTON, lambda e: self.onBatchAssoc(assoc=False), dissoc_btn)

    def getButtons(self, parent):
        btnsizer = wx.StdDialogButtonSizer()
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("&Close"))
        btnsizer.AddButton(cancelBtn)
        btnsizer.Realize()
        self.Bind(wx.EVT_BUTTON, lambda e: self.Close(), id=wx.ID_CANCEL)
        return btnsizer

    def onFileAssoc(self, ext, desc):
        shell_integrate((ext,))
        wx.MessageBox(
            # Translators: the text of a message indicating successful file association
            _("Files of type {format} have been associated with Bookworm.").format(
                format=desc
            ),
            # Translators: the title of a message indicating successful file association
            _("Success"),
            style=wx.ICON_INFORMATION,
        )

    def onBatchAssoc(self, assoc):
        func = shell_integrate if assoc else shell_disintegrate
        func()
        if assoc:
            # Translators: the text of a message indicating successful removal of file associations
            msg = _(
                "All supported file types have been set to open by default in Bookworm."
            )
        else:
            # Translators: the text of a message indicating successful removal of file associations
            msg = _("All registered file associations have been removed.")
        wx.MessageBox(
            msg,
            # Translators: the title of a message indicating successful removal of file association
            _("Success"),
            style=wx.ICON_INFORMATION,
        )
        self.Close()

    def Close(self):
        config.conf["history"]["set_file_assoc"] = -1
        config.save()
        super().Close()
        self.Destroy()
        if self.standalone:
            wx.GetApp().ExitMainLoop()
            sys.exit(0)


def show_file_association_dialog():
    config.setup_config()
    wx_app = wx.App()
    dlg = FileAssociationDialog(None, standalone=True)
    wx_app.SetTopWindow(dlg)
    dlg.Show()
    wx_app.MainLoop()


@app_started.connect
def _on_app_first_run(sender):
    if not app.is_frozen or IS_RUNNING_PORTABLE:
        return
    ndoctypes = len(get_ext_info())
    confval = config.conf["history"]["set_file_assoc"]
    if (confval >= 0) and (confval != ndoctypes):
        dlg = FileAssociationDialog(wx.GetApp().mainFrame)
        wx.CallAfter(dlg.ShowModal)
        config.conf["history"]["set_file_assoc"] = ndoctypes
        config.save()


class SettingsPanel(sc.SizedPanel):

    config_section = None

    def __init__(self, parent, settings_dialog=None, config_object=None):
        super().__init__(parent, -1)
        config_object = config_object or config.conf.config
        self.config = config_object[self.config_section]
        self.settings_dialog = settings_dialog
        self.addControls()

    def addControls(self):
        raise NotImplementedError

    def get_state(self):
        for key, value in self.config.items():
            ctrl = self.FindWindowByName(f"{self.config_section}.{key}")
            if not ctrl:
                continue
            yield ctrl, key, value

    def reconcile(self, strategy=ReconciliationStrategies.load):
        for ctrl, key, value in self.get_state():
            if strategy is ReconciliationStrategies.load:
                ctrl.SetValue(value)
            elif strategy is ReconciliationStrategies.save:
                self.config[key] = ctrl.GetValue()
        if strategy is ReconciliationStrategies.save:
            config.save()
            config_updated.send(self, section=self.config_section)

    def make_static_box(self, title, parent=None, ctrl_id=-1):
        stbx = sc.SizedStaticBox(parent or self, ctrl_id, title)
        stbx.SetSizerProp("expand", True)
        stbx.Sizer.AddSpacer(25)
        return stbx


class GeneralPanel(SettingsPanel):
    config_section = "general"

    def addControls(self):
        # Translators: the title of a group of controls in the
        # general settings page related to the UI
        UIBox = self.make_static_box(_("User Interface"))
        # Translators: the label of a combobox containing display languages.
        wx.StaticText(UIBox, -1, _("Display Language:"))
        self.languageChoice = wx.Choice(UIBox, -1, style=wx.CB_SORT)
        self.languageChoice.SetSizerProps(expand=True)
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak user interface messages"),
            name="general.announce_ui_messages",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak page number"),
            name="general.speak_page_number",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Speak section title"),
            name="general.speak_section_title",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Play pagination sound"),
            name="general.play_pagination_sound",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Include page label in page title"),
            name="general.include_page_label",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Use file name instead of book title"),
            name="general.show_file_name_as_title",
        )
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Show reading progress percentage"),
            name="general.show_reading_progress_percentage",
        )
        # Translators: the title of a group of controls shown in the
        # general settings page related to miscellaneous settings
        miscBox = self.make_static_box(_("Miscellaneous"))
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Open recently opened books from the last position"),
            name="general.open_with_last_position",
        )
        wx.CheckBox(
            miscBox,
            -1,
            # Translators: the label of a checkbox
            _("Automatically check for updates"),
            name="general.auto_check_for_updates",
        )
        if not IS_RUNNING_PORTABLE:
            # Translators: the title of a group of controls shown in the
            # general settings page related to file associations
            assocBox = self.make_static_box(_("File Associations"))
            wx.Button(
                assocBox,
                wx.ID_SETUP,
                # Translators: the label of a button
                _("Manage File &Associations"),
            )
            self.Bind(wx.EVT_BUTTON, self.onRequestFileAssoc, id=wx.ID_SETUP)
        languages = [l for l in set(get_available_locales().values())]
        for langobj in languages:
            self.languageChoice.Append(langobj.description, langobj)
        self.languageChoice.SetStringSelection(app.current_language.description)

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.save:
            selection = self.languageChoice.GetSelection()
            if selection == wx.NOT_FOUND:
                return
            selected_lang = self.languageChoice.GetClientData(selection)
            if selected_lang.pylang != app.current_language.pylang:
                self.config["language"] = selected_lang.pylang
                config.save()
                set_locale(selected_lang.pylang)
                msg = wx.MessageBox(
                    # Translators: the content of a message asking the user to restart
                    _(
                        "You have changed the display language of Bookworm.\n"
                        "For this setting to fully take effect, you need to restart the application.\n"
                        "Would you like to restart the application right now?"
                    ),
                    # Translators: the title of a message telling the user
                    # that the display language have been changed
                    _("Language Changed"),
                    style=wx.YES_NO | wx.ICON_WARNING,
                )
                if msg == wx.YES:
                    restart_application()
        super().reconcile(strategy=strategy)

    def onRequestFileAssoc(self, event):
        with FileAssociationDialog(self) as dlg:
            dlg.ShowModal()


class AppearancePanel(SettingsPanel):
    config_section = "appearance"

    def __init__(self, *args, **kwargs):
        self.font_enumerator = wx.FontEnumerator()
        super().__init__(*args, **kwargs)

    def addControls(self):
        # Translators: the title of a group of controls in the
        # appearance settings page related to the UI
        GeneralAppearanceBox = self.make_static_box(_("General Appearance"))
        wx.CheckBox(
            GeneralAppearanceBox,
            -1,
            # Translators: the label of a checkbox
            _("Maximize the application window upon startup"),
            name="appearance.start_maximized",
        )
        UIBox = self.make_static_box(_("Text Styling"))
        wx.CheckBox(
            UIBox,
            -1,
            # Translators: the label of a checkbox
            _("Apply text styling (when available)"),
            name="appearance.apply_text_styles",
        )
        # Translators: the title of a group of controls in the
        # appearance settings page related to the UI
        fontBox = self.make_static_box(_("Font"))
        # Translators: label of a combobox
        wx.StaticText(fontBox, -1, _("Font Face"))
        self.fontChoice = wx.Choice(
            fontBox,
            -1,
            choices=self.get_available_fonts(),
        )
        self.useOpendyslexicFontCheckBox = wx.CheckBox(
            fontBox,
            -1,
            # Translators: label of a checkbox
            _("Use Open-&dyslexic font"),
            name="appearance.use_opendyslexic_font",
        )
        # Translators: label of an edit box
        wx.StaticText(fontBox, -1, _("Font Size"))
        EnhancedSpinCtrl(fontBox, -1, min=10, max=96, name="appearance.font_point_size")
        wx.CheckBox(
            fontBox,
            -1,
            # Translators: the label of a checkbox
            _("Bold style"),
            name="appearance.use_bold_font",
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            self.onUseOpendyslexicFontCheckBox,
            self.useOpendyslexicFontCheckBox,
        )

    def onUseOpendyslexicFontCheckBox(self, event):
        if event.IsChecked():
            self.fontChoice.SetStringSelection("OpenDyslexic")
            self.fontChoice.Enable(False)
        else:
            self.fontChoice.SetStringSelection(self.config["font_facename"])
            self.fontChoice.Enable(True)

    def reconcile(self, strategy=ReconciliationStrategies.load):
        if strategy is ReconciliationStrategies.load:
            if (
                configured_fontface := self.config["font_facename"]
            ) and self.font_enumerator.IsValidFacename(configured_fontface):
                self.fontChoice.SetStringSelection(configured_fontface)
            else:
                self.fontChoice.SetSelection(0)
        elif strategy is ReconciliationStrategies.save:
            self.config["font_facename"] = self.fontChoice.GetStringSelection()
        super().reconcile(strategy=strategy)
        if strategy is ReconciliationStrategies.save:
            wx.GetApp().mainFrame.set_content_view_font()
        else:
            if self.useOpendyslexicFontCheckBox.IsChecked():
                self.fontChoice.Enable(False)

    def get_available_fonts(self):
        self.font_enumerator.EnumerateFacenames()
        return tuple(
            filter(
                lambda face: not face.startswith("@") and not face[0].isdigit(),
                sorted(self.font_enumerator.GetFacenames()),
            )
        )


class PreferencesDialog(SimpleDialog):
    """Preferences dialog."""

    def addPanels(self):
        page_info = [
            # Translators: the label of a page in the settings dialog
            (0, "general", GeneralPanel, _("General")),
            # Translators: the label of a page in the settings dialog
            (1, "appearance", AppearancePanel, _("Appearance")),
        ]
        page_info.extend(wx.GetApp().service_handler.get_settings_panels())
        page_info.sort()
        image_list = wx.ImageList(24, 24)
        self.tabs.AssignImageList(image_list)
        for idx, (__, image, panel_cls, label) in enumerate(page_info):
            bmp = getattr(app_icons, image).GetBitmap()
            image_list.Add(bmp)
            # Create settings page
            page = panel_cls(self.tabs, self)
            # Add tabs
            self.tabs.AddPage(page, label, select=(idx == 0), imageId=idx)

    def addControls(self, parent):
        self.tabs = wx.Listbook(parent, -1)
        self.addPanels()
        # Finalize
        self.SetButtonSizer(self.createButtonsSizer())
        # Event handlers
        self.Bind(wx.EVT_BUTTON, self.onSubmit, id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onApply, id=wx.ID_APPLY)
        self.Bind(wx.EVT_BUTTON, lambda e: self.Destroy(), id=wx.ID_CANCEL)

        # Initialize values
        self.reconcile_all(ReconciliationStrategies.load)
        self.tabs.GetListView().SetFocus()
        # Translators: label of the settings categories list box
        self.tabs.GetListView().SetLabel(_("Categories"))

    def getButtons(self, parent):
        return

    def reconcile_all(self, strategy):
        for num in range(0, self.tabs.GetPageCount()):
            page = self.tabs.GetPage(num)
            page.reconcile(strategy)

    def onSubmit(self, event):
        page = self.tabs.GetCurrentPage()
        page.reconcile(strategy=ReconciliationStrategies.save)
        self.Close()
        self.Destroy()

    def onApply(self, event):
        page = self.tabs.GetCurrentPage()
        page.reconcile(strategy=ReconciliationStrategies.save)
        self.tabs.GetListView().SetFocus()

    def createButtonsSizer(self):
        btnsizer = wx.StdDialogButtonSizer()
        # Translators: the label of the OK button in a dialog
        okBtn = wx.Button(self, wx.ID_OK, _("OK"))
        okBtn.SetDefault()
        # Translators: the label of the cancel button in a dialog
        cancelBtn = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        # Translators: the label of the apply button in a dialog
        applyBtn = wx.Button(self, wx.ID_APPLY, _("Apply"))
        for btn in (okBtn, cancelBtn, applyBtn):
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        return btnsizer
