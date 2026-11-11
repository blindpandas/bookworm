"""Lazy audiobook service: an unavailable audio engine never prevents reading text."""

from typing import ClassVar

import wx

from bookworm.service import BookwormService


class AudiobookService(BookwormService):
    name = "audiobooks"
    has_gui = True
    config_spec: ClassVar[dict] = {
        "audiobooks": {
            "short_skip_seconds": "integer(min=1, max=60, default=10)",
            "long_skip_seconds": "integer(min=10, max=600, default=60)",
            "resume_rewind_seconds": "integer(min=0, max=30, default=0)",
        }
    }

    def __post_init__(self):
        self.window = None
        self.media_active = False
        self.menu_id = int(wx.NewIdRef())
        self.view.Bind(wx.EVT_MENU, self.show, id=self.menu_id)
        self.view.Bind(wx.EVT_CLOSE, self.on_parent_close)

    def process_menubar(self, _menubar):
        self.view.fileMenu.Insert(2, self.menu_id, _("&Audiobooks…\tCtrl+F11"))

    def get_keyboard_shortcuts(self):
        return {self.menu_id: "Ctrl+F11"}

    def show(self, _event=None):
        if self.window is None:
            from .gui import AudiobookWindow

            try:
                self.window = AudiobookWindow(self.view, self.on_window_closed)
            except Exception as exc:
                wx.MessageBox(str(exc), _("Audiobooks"), wx.OK | wx.ICON_ERROR, self.view)
                return
        self.window.Show()
        self.window.Raise()

    def on_window_closed(self):
        self.window = None

    def on_parent_close(self, event):
        if self.window is not None and not self.window.Close() and event.CanVeto():
            event.Veto()
            return
        event.Skip()

    def shutdown(self):
        if self.window is not None:
            self.window.Close()

    def handle_media_key(self, key):
        if not self.media_active or self.window is None or self.window.player.book is None:
            return False
        action = {
            "play_pause": self.window.toggle,
            "next": lambda: self.window.skip(1),
            "previous": lambda: self.window.skip(-1),
        }.get(key)
        if action:
            self.window.guarded(action)
            return True
        return False

    def pause_for_tts(self):
        self.media_active = False
        if self.window is not None and self.window.player.book is not None:
            self.window.guarded(self.window.player.pause)
