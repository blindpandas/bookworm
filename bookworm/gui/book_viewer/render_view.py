# coding: utf-8

from pathlib import Path

import wx
import wx.lib.scrolledpanel as scrolled

from bookworm import speech
from bookworm.gui.components import ImageViewControl
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


class EmbeddedImageDialog(wx.Dialog):
    """Show an image embedded in a book."""

    ID_RESET_ZOOM = wx.NewIdRef()
    MIN_ZOOM = 0.1
    MAX_ZOOM = 10.0
    SAVE_FORMAT_CHOICES = (("PNG", ".png"), ("JPEG", ".jpg"))

    def __init__(
        self,
        parent,
        title,
        image_io: ImageIO,
        suggested_filename="image.png",
        size=(700, 600),
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
    ):
        super().__init__(parent, title=title, size=size, style=style)
        bg_color = (215, 215, 215) if not IS_HIGH_CONTRAST_ACTIVE else (30, 30, 30)
        self.SetBackgroundColour(wx.Colour(bg_color))
        self.parent = parent
        self.image_io = image_io
        self.suggested_filename = self._normalize_suggested_filename(
            suggested_filename
        )
        self.scaling_factor = 0.2
        self._zoom_factor = 1.0
        self._build_controls()
        self.setDialogImage()
        self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)
        self.CenterOnParent()

    def _build_controls(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        toolbar = wx.ToolBar(self, -1, style=wx.TB_FLAT | wx.TB_HORIZONTAL)
        self._add_tool(toolbar, wx.ID_ZOOM_IN, _("Zoom In"), wx.ART_PLUS)
        self._add_tool(toolbar, wx.ID_ZOOM_OUT, _("Zoom Out"), wx.ART_MINUS)
        self._add_tool(toolbar, self.ID_RESET_ZOOM, _("Actual Size"), wx.ART_GO_HOME)
        toolbar.AddSeparator()
        self._add_tool(toolbar, wx.ID_SAVE, _("Save As"), wx.ART_FILE_SAVE)
        self._add_tool(toolbar, wx.ID_COPY, _("Copy"), wx.ART_COPY)
        toolbar.AddSeparator()
        self._add_tool(toolbar, wx.ID_CLOSE, _("Close"), wx.ART_CLOSE)
        toolbar.Realize()
        sizer.Add(toolbar, 0, wx.EXPAND)

        self.scroll = scrolled.ScrolledPanel(self, -1, name=_("Image"), style=0)
        self.scroll.SetTransparent(0)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        self.imageCtrl = ImageViewControl(self.scroll, -1)
        panel_sizer.Add(self.imageCtrl, 1, wx.CENTER | wx.BOTH)
        self.scroll.SetSizer(panel_sizer)
        sizer.Add(self.scroll, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_TOOL, lambda event: self.set_zoom(1), id=wx.ID_ZOOM_IN)
        self.Bind(wx.EVT_TOOL, lambda event: self.set_zoom(-1), id=wx.ID_ZOOM_OUT)
        self.Bind(wx.EVT_TOOL, lambda event: self.set_zoom(0), id=self.ID_RESET_ZOOM)
        self.Bind(wx.EVT_TOOL, self.onSaveImage, id=wx.ID_SAVE)
        self.Bind(wx.EVT_TOOL, self.onCopyImage, id=wx.ID_COPY)
        self.Bind(wx.EVT_TOOL, lambda event: self.Close(), id=wx.ID_CLOSE)

    def _add_tool(self, toolbar, tool_id, label, art_id):
        bitmap = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16, 16))
        toolbar.AddTool(tool_id, label, bitmap)
        toolbar.SetToolShortHelp(tool_id, label)

    def _normalize_suggested_filename(self, suggested_filename):
        filename = Path(suggested_filename or "image.png").name or "image.png"
        if not Path(filename).suffix:
            filename = f"{filename}.png"
        return filename

    @property
    def scroll_rate_x(self):
        return max(1, round(self.imageCtrl.Size[0] * 0.05))

    @property
    def scroll_rate_y(self):
        return max(1, round(self.imageCtrl.Size[1] * 0.025))

    def set_zoom(self, val):
        if val == 0:
            self.zoom_factor = 1.0
        else:
            self.zoom_factor += val * self.scaling_factor

    @property
    def zoom_factor(self):
        return self._zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, value):
        if (value < self.MIN_ZOOM) or (value > self.MAX_ZOOM):
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
        image = self.getRenderedImage()
        self.imageCtrl.RenderImageIO(image)
        self.scroll.SetupScrolling(
            rate_x=self.scroll_rate_x, rate_y=self.scroll_rate_y, scrollToTop=False
        )
        if reset_scroll_pos:
            wx.CallLater(50, self.scroll.Scroll, 0, 0)
        self.scroll.SetFocus()

    def getRenderedImage(self):
        if self.zoom_factor == 1.0:
            return self.image_io
        width = max(1, round(self.image_io.width * self.zoom_factor))
        height = max(1, round(self.image_io.height * self.zoom_factor))
        return ImageIO.from_pil(self.image_io.to_pil().resize((width, height)))

    def onCharHook(self, event):
        keycode = event.GetKeyCode()
        modifiers = event.GetModifiers()
        if keycode == wx.WXK_ESCAPE:
            self.Close()
            return
        if modifiers != wx.MOD_CONTROL:
            event.Skip()
            return
        if keycode == ord("="):
            self.set_zoom(1)
        elif keycode == ord("-"):
            self.set_zoom(-1)
        elif keycode == ord("0"):
            self.set_zoom(0)
        elif keycode == ord("S"):
            self.onSaveImage(event)
        elif keycode == ord("C"):
            self.onCopyImage(event)
        else:
            event.Skip()

    def onSaveImage(self, event):
        with wx.FileDialog(
            self,
            # Translators: title of a save file dialog for an embedded book image
            _("Save Image"),
            defaultDir=wx.GetUserHome(),
            defaultFile=self.suggested_filename,
            wildcard=_("PNG Image") + " (*.png)|*.png|"
            + _("JPEG Image")
            + " (*.jpg)|*.jpg",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as save_dialog:
            if save_dialog.ShowModal() != wx.ID_OK:
                return
            selected_path = save_dialog.GetPath()
            output_path, image_format = self.get_save_target(
                selected_path, save_dialog.GetFilterIndex()
            )
        if not self.confirm_overwrite_after_suffix_normalization(
            selected_path,
            output_path,
        ):
            return
        try:
            pil_image = self.prepare_image_for_save(
                self.image_io.to_pil(),
                image_format,
            )
            pil_image.save(output_path, format=image_format)
        except Exception:
            log.exception("Failed to save embedded image.", exc_info=True)
            wx.MessageBox(
                _("Could not save this image."),
                _("Save Image"),
                style=wx.ICON_ERROR,
                parent=self,
            )
        else:
            speech.announce(_("Image saved"), True)

    @staticmethod
    def prepare_image_for_save(pil_image, image_format):
        if image_format == "JPEG":
            return pil_image.convert("RGB")
        if image_format == "PNG" and pil_image.mode not in {
            "1",
            "L",
            "LA",
            "P",
            "RGB",
            "RGBA",
            "I",
            "I;16",
        }:
            output_mode = "RGBA" if "A" in pil_image.getbands() else "RGB"
            return pil_image.convert(output_mode)
        return pil_image

    @classmethod
    def get_save_target(cls, path, filter_index):
        index = (
            filter_index if 0 <= filter_index < len(cls.SAVE_FORMAT_CHOICES) else 0
        )
        image_format, suffix = cls.SAVE_FORMAT_CHOICES[index]
        output_path = Path(path)
        if output_path.suffix.lower() != suffix:
            output_path = output_path.with_suffix(suffix)
        return output_path, image_format

    def confirm_overwrite_after_suffix_normalization(self, selected_path, output_path):
        if not self.should_confirm_overwrite_after_suffix_normalization(
            selected_path,
            output_path,
        ):
            return True
        retval = wx.MessageBox(
            # Translators: content of a message confirming overwrite of an image file
            _(
                'A file named "{filename}" already exists. Do you want to replace it?'
            ).format(
                filename=Path(output_path).name,
            ),
            # Translators: title of a message confirming overwrite of an image file
            _("Confirm Save As"),
            style=wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
            parent=self,
        )
        return retval == wx.YES

    @staticmethod
    def should_confirm_overwrite_after_suffix_normalization(
        selected_path,
        output_path,
    ):
        selected_path = Path(selected_path)
        output_path = Path(output_path)
        return output_path != selected_path and output_path.exists()

    def onCopyImage(self, event):
        try:
            if not wx.TheClipboard.Open():
                raise RuntimeError("Could not open the clipboard")
            try:
                data = wx.BitmapDataObject()
                data.SetBitmap(self.image_io.to_wx_bitmap())
                wx.TheClipboard.SetData(data)
            finally:
                wx.TheClipboard.Close()
        except Exception:
            log.exception("Failed to copy embedded image.", exc_info=True)
            wx.MessageBox(
                _("Could not copy this image."),
                _("Copy Image"),
                style=wx.ICON_ERROR,
                parent=self,
            )
        else:
            speech.announce(_("Image copied to clipboard"), True)
