# coding: utf-8

import wx
import wx.lib.scrolledpanel as scrolled
from bookworm import speech
from bookworm.image_io import ImageIO
from bookworm.signals import reader_page_changed
from bookworm.runtime import IS_HIGH_CONTRAST_ACTIVE
from bookworm.utils import gui_thread_safe
from bookworm.logger import logger
from bookworm.gui.components import Dialog
from .navigation import NavigationProvider


log = logger.getChild(__name__)


class ImageView(wx.Control):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        # Bind events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.ClearBackground()
        self.data = (wx.NullBitmap, 0, 0)

    def AcceptsFocus(self):
        return False

    def OnPaint(self, event):
        bmp, width, height = self.data
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush("white"))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        gc.DrawBitmap(bmp, 0, 0, width, height)

    def RenderImage(self, bmp, width, height):
        self.SetInitialSize(wx.Size(width, height))
        self.data = (bmp, width, height)
        self.Refresh()


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
        self._zoom_factor = 1
        # Translators: the label of the image of a page in a dialog to render the current page
        panel = self.scroll = scrolled.ScrolledPanel(self, -1, name=_("Page"), style=0)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.imageCtrl = ImageView(panel, -1)
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
        panel.SetupScrolling(rate_x=self.scroll_rate_x, rate_y=self.scroll_rate_y)
        self._currently_rendered_page = self.reader.current_page
        reader_page_changed.connect(self.onPageChange, sender=self.reader)

    @property
    def scroll_rate_x(self):
        return self.imageCtrl.Size[0] * 0.05

    @property
    def scroll_rate_y(self):
        return self.imageCtrl.Size[1] * 0.025

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

    def onKeyUp(self, event):
        event.Skip()
        code = event.GetKeyCode()
        if code == wx.WXK_ESCAPE:
            self.Close()
            self.Destroy()

    def Close(self, *args, **kwargs):
        super().Close(*args, **kwargs)
        reader_page_changed.disconnect(self.onPageChange, sender=self.reader)
