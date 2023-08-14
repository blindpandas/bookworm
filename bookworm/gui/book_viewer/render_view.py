# coding: utf-8

import wx
import wx.lib.scrolledpanel as scrolled

from bookworm import speech
from bookworm.gui.components import Dialog, ImageViewControl
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.runtime import IS_HIGH_CONTRAST_ACTIVE
from bookworm.signals import reader_page_changed
from bookworm.utils import gui_thread_safe

from .navigation import NavigationProvider

log = logger.getChild(__name__)


class ViewPageAsImageDialog(wx.Dialog):
    """Show the page rendered as an image."""

    def __init__(self, parent, title, size=(450, 450), style=wx.DEFAULT_DIALOG_STYLE):
        super().__init__(parent, title=title, style=style)
        bg_color = (215, 215, 215) if not IS_HIGH_CONTRAST_ACTIVE else (30, 30, 30)
        self.SetBackgroundColour(wx.Colour(bg_color))
        self.parent = parent
        self.reader = self.parent.reader
        # Zoom support
        self.scaling_factor = 0.2
        self._zoom_factor = 1.5
        # Translators: the label of the image of a page in a dialog to render the current page
        panel = self.scroll = scrolled.ScrolledPanel(self, -1, name=_("Page"), style=0)
        panel.SetTransparent(0)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.imageCtrl = ImageViewControl(panel, -1)
        sizer.Add(self.imageCtrl, 1, wx.CENTER | wx.BOTH)
        panel.SetSizer(sizer)
        sizer.Fit(panel)
        panel.Layout()
        self.setDialogImage()
        NavigationProvider(
            ctrl=panel,
            reader=self.reader,
            callback_func=self.setDialogImage,
            zoom_callback=self.set_zoom,
        )
        panel.Bind(wx.EVT_KEY_UP, self.onKeyUp, panel)
        panel.Bind(wx.EVT_CHAR_HOOK, self.onScrollChar, panel)
        panel.SetupScrolling(rate_x=self.scroll_rate_x, rate_y=self.scroll_rate_y)
        self._currently_rendered_page = self.reader.current_page
        reader_page_changed.connect(self.onPageChange, sender=self.reader)

    @property
    def scroll_rate_x(self):
        return round(self.imageCtrl.Size[0] * 0.05)

    @property
    def scroll_rate_y(self):
        return round(self.imageCtrl.Size[1] * 0.025)

    @gui_thread_safe
    def onPageChange(self, sender, current, prev):
        if self._currently_rendered_page != current:
            self.setDialogImage()

    def set_zoom(self, val):
        if val == 0:
            self.zoom_factor = 1
        else:
            self.zoom_factor += val * self.scaling_factor

    @property
    def zoom_factor(self):
        return self._zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, value):
        if (value < 1.0) or (value > 10.0):
            return
        self._zoom_factor = value
        self.setDialogImage(reset_scroll_pos=False)
        self.scroll.SetupScrolling(
            rate_x=self.scroll_rate_x, rate_y=self.scroll_rate_y, scrollToTop=False
        )
        # Translators: a message announced to the user when the zoom factor changes
        speech.announce(
            _("Zoom is at {factor} percent").format(factor=int(value * 100))
        )

    def setDialogImage(self, reset_scroll_pos=True):
        bmp, size = self.getPageImage()
        self.imageCtrl.RenderImage(bmp, *size)
        self._currently_rendered_page = self.reader.current_page
        if reset_scroll_pos:
            self.scroll.SetupScrolling(
                rate_x=self.scroll_rate_x, rate_y=self.scroll_rate_y, scrollToTop=False
            )
            wx.CallLater(50, self.scroll.Scroll, 0, 0)
        self.scroll.SetName(_("Page {}").format(self._currently_rendered_page))

    def getPageImage(self):
        image = self.reader.document.get_page_image(
            self.reader.current_page, zoom_factor=self._zoom_factor
        )
        if IS_HIGH_CONTRAST_ACTIVE:
            image = image.invert()
        bmp = image.to_wx_bitmap()
        return bmp, image.size

    def onScrollChar(self, event):
        if event.KeyCode != wx.WXK_TAB:
            event.Skip()

    def onKeyUp(self, event):
        event.Skip()
        code = event.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.Close()
            self.Destroy()

    def Close(self, *args, **kwargs):
        super().Close(*args, **kwargs)
        reader_page_changed.disconnect(self.onPageChange, sender=self.reader)
