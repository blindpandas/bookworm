"""Real wx widgets and accelerators; BOOKWORM_TEST_GUI=1, a desktop required.

These checks do not replace Windows screen-reader listening tests.
"""

import os
import sys
import time
import types
import wave
from threading import Event

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("BOOKWORM_TEST_GUI") != "1", reason="Native GUI tests are opt-in"
)


@pytest.fixture
def window(tmp_path, monkeypatch):
    import wx

    import bookworm

    config = types.ModuleType("bookworm.config")
    config.conf = {
        "audiobooks": {
            "short_skip_seconds": 10,
            "long_skip_seconds": 60,
            "resume_rewind_seconds": 5,
        }
    }
    config.save = lambda: None
    spoken = []
    speech = types.ModuleType("bookworm.speech")
    speech.announce = spoken.append
    paths = types.ModuleType("bookworm.paths")
    paths.data_path = lambda *parts: tmp_path.joinpath(*parts)
    for module in (config, speech, paths):
        monkeypatch.setitem(sys.modules, module.__name__, module)
        monkeypatch.setattr(bookworm, module.__name__.split(".")[-1], module, raising=False)
    from bookworm.audiobooks import gui
    from bookworm.audiobooks.backend import MpvAudioBackend
    from bookworm.audiobooks.importer import import_book

    for name, module in (("config", config), ("speech", speech)):
        monkeypatch.setattr(gui, name, module)
    monkeypatch.setattr(gui, "data_path", paths.data_path)
    app = wx.GetApp() or wx.App(False)
    # These tests run outside app.MainLoop(). On MSW, app.Yield() dispatches
    # native input through EventLoopBase.GetActive(); a temporary, unactivated
    # loop does not dispatch the queued keyboard messages. GTK hid this error.
    event_loop = wx.GUIEventLoop()
    loop_activator = wx.EventLoopActivator(event_loop)
    assert wx.EventLoopBase.GetActive() == event_loop
    frame = gui.AudiobookWindow(None, lambda: None)
    frame.player.backend = MpvAudioBackend(wx.CallAfter, ao="null")
    source = tmp_path / "test.wav"
    with wave.open(str(source), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(8000)
        file.writeframes(b"\0\0" * 8000 * 120)
    book = import_book(source)
    frame.library.add(book)
    frame.refresh_books()
    frame.Show()
    frame.Raise()
    frame.books.SetFocus()
    frame.open_selected()
    deadline = time.monotonic() + 5
    while not frame.player._ready and time.monotonic() < deadline:
        app.Yield()
        time.sleep(0.01)
    assert frame.player._ready
    spoken.clear()
    yield frame, spoken, app
    frame.Close()
    app.Yield()
    del loop_activator


def pump(app, duration=0.1):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        app.Yield()
        time.sleep(0.005)


def test_native_controls_and_no_duplicate_volume_speech(window):

    frame, spoken, app = window
    assert frame.volume.GetName() == "Volume (%)"
    assert frame.speed.GetName() == "Speed (%)"
    frame.volume.SetFocus()
    pump(app)
    frame.volume.Value = 70
    frame.apply_volume()
    assert frame.player.volume == 0.7
    assert not spoken
    frame.change_volume(0.05)
    assert not spoken
    frame.books.SetFocus()
    pump(app)
    frame.change_volume(0.05)
    assert len(spoken) == 1
    assert "80%" in spoken[0]


def test_real_menu_accelerators_respond_without_reloading(window, monkeypatch):
    import wx

    from bookworm.audiobooks.player import State

    frame, _spoken, app = window
    simulator = wx.UIActionSimulator()
    # SendInput on Windows goes to the foreground window. A native click
    # activates this test window before testing the real accelerator route.
    point = frame.books.ClientToScreen((10, 10))
    assert simulator.MouseMove(point.x, point.y)
    assert simulator.MouseClick()
    pump(app)
    assert frame.IsActive(), "The test window did not receive desktop activation"
    frame.books.SetFocus()
    pump(app)
    assert simulator.KeyDown(wx.WXK_F5)
    assert simulator.KeyUp(wx.WXK_F5)
    pump(app)
    assert frame.player.state is State.PLAYING
    assert simulator.KeyDown(wx.WXK_F6)
    assert simulator.KeyUp(wx.WXK_F6)
    pump(app)
    assert frame.player.state is State.PAUSED
    control = frame.player.backend.control
    # Time the native input dispatch plus the real command handler. Yield also
    # processes unrelated paint/timer events after the handler has completed;
    # their duration is not keyboard command latency.
    completed = []
    real_skip = frame.skip

    def timed_skip(*args, **kwargs):
        result = real_skip(*args, **kwargs)
        completed.append(time.monotonic())
        return result

    monkeypatch.setattr(frame, "skip", timed_skip)
    started = time.monotonic()
    assert simulator.KeyDown(wx.WXK_F8)
    assert simulator.KeyUp(wx.WXK_F8)
    pump(app)
    assert 10000 <= frame.player.position_ms < 11000
    assert frame.player.backend.control is control
    assert len(completed) == 1
    assert completed[0] - started < 0.75
    stop = wx.FindWindowByName("Stop", frame)
    assert isinstance(stop, wx.Button)
    assert simulator.KeyDown(wx.WXK_F9)
    assert simulator.KeyUp(wx.WXK_F9)
    pump(app)
    assert frame.player.state is State.STOPPED
    assert frame.player.position_ms == 0
    assert frame.player.backend.control is None
    assert simulator.KeyDown(wx.WXK_F5)
    assert simulator.KeyUp(wx.WXK_F5)
    deadline = time.monotonic() + 2
    while frame.player.state is not State.PLAYING and time.monotonic() < deadline:
        pump(app, 0.01)
    assert frame.player.state is State.PLAYING
    assert frame.player.position_ms < 1000
    assert frame.player.backend.control is not control


def test_seek_command_remains_responsive_while_position_disk_write_is_blocked(window, monkeypatch):
    import wx

    frame, _spoken, app = window
    frame.player.checkpoint()
    writer = frame.library.position_writer
    persist = writer._persist
    entered, release = Event(), Event()

    def blocked(connection, updates):
        entered.set()
        assert release.wait(5), "Test did not release the position writer"
        persist(connection, updates)

    monkeypatch.setattr(writer, "_persist", blocked)
    completed = []
    real_skip = frame.skip

    def timed_skip(*args, **kwargs):
        result = real_skip(*args, **kwargs)
        completed.append(time.monotonic())
        return result

    monkeypatch.setattr(frame, "skip", timed_skip)
    try:
        frame.player.seek(1000)
        assert entered.wait(2)
        frame.books.SetFocus()
        pump(app)
        simulator = wx.UIActionSimulator()
        started = time.monotonic()
        assert simulator.KeyDown(wx.WXK_F8)
        assert simulator.KeyUp(wx.WXK_F8)
        pump(app)
        assert len(completed) == 1
        assert completed[0] - started < 0.75
        assert frame.player.position_ms == 11000
        assert not release.is_set()
    finally:
        release.set()
    frame.library.flush_positions()
    assert frame.library.state(frame.player.book.id)["position"] == 11000


def test_position_writer_error_stops_audio_and_has_one_error_dialog(window, monkeypatch):
    import wx

    from bookworm.audiobooks.player import State

    frame, _spoken, _app = window
    frame.player.checkpoint()
    dialogs = []

    def message_box(message, title, style, *_args):
        dialogs.append((message, title))
        return wx.YES if style & wx.YES_NO else wx.OK

    monkeypatch.setattr(wx, "MessageBox", message_box)

    def fail(_connection, _updates):
        raise OSError("disk full")

    monkeypatch.setattr(frame.library.position_writer, "_persist", fail)
    frame.player.play()
    frame.player.seek(1234)
    frame.library.position_writer.thread.join(timeout=2)
    frame.guarded(lambda: frame.change_volume(0.05))
    assert frame.player.state is State.ERROR
    assert frame.player.backend.control is None
    assert len(dialogs) == 1
    assert "listening position could not be saved" in dialogs[0][0]
    frame.on_timer(None)
    assert len(dialogs) == 1


def test_dialogs_construct_and_export_choices_are_native(window):
    import wx

    from bookworm.audiobooks.gui import (
        AudioSettingsDialog,
        BookmarkEditor,
        BookmarksDialog,
        ExportDialog,
        ImportPreview,
    )

    frame, _spoken, app = window
    for kind, args in (
        (AudioSettingsDialog, (frame,)),
        (BookmarkEditor, (frame,)),
        (BookmarksDialog, (frame,)),
        (ExportDialog, (frame,)),
        (ImportPreview, (frame, frame.player.book)),
    ):
        dialog = kind(*args)
        dialog.Show()
        pump(app)
        if isinstance(dialog, ExportDialog):
            assert isinstance(dialog.format, wx.Choice)
            assert dialog.format.GetName() == "Audio format"
            assert dialog.bitrate.IsEnabled()
            dialog.format.SetSelection(2)
            dialog.update_bitrate(None)
            assert not dialog.bitrate.IsEnabled()
        dialog.Hide()
        dialog.Destroy()
        pump(app)


def test_shortcuts_are_unique_and_leave_standard_text_editing_available(window):
    import wx

    frame, _spoken, _app = window
    assert len(frame.shortcut_index) >= 20
    forbidden = {(wx.ACCEL_CTRL, ord(letter)) for letter in "ACVXYZ"}
    forbidden.update(
        (wx.ACCEL_CTRL, key)
        for key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_HOME, wx.WXK_END)
    )
    forbidden.update(
        (wx.ACCEL_CTRL | wx.ACCEL_SHIFT, key)
        for key in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT, wx.WXK_RIGHT)
    )
    # Ctrl+Alt+printable keys can consume AltGr characters on Windows.
    forbidden.update((wx.ACCEL_CTRL | wx.ACCEL_ALT, key) for key in range(32, 127))
    assert not forbidden.intersection(frame.shortcut_index)


def test_tag_windows_show_real_controls_and_empty_tags_are_not_invented(window):
    from bookworm.audiobooks.metadata import TagDocument
    from bookworm.audiobooks.metadata_gui import FileInformationDialog, TagEditorDialog, V1Dialog

    frame, _spoken, app = window
    document = TagDocument.read(frame.player.book.absolute_path(0))
    assert not document.has_v2
    for kind, args in (
        (FileInformationDialog, (frame, document)),
        (TagEditorDialog, (frame, document)),
        (V1Dialog, (frame, b"")),
    ):
        dialog = kind(*args)
        dialog.Show()
        pump(app)
        if isinstance(dialog, TagEditorDialog):
            assert dialog.tree.GetName() == "Audio tag fields"
            assert dialog.tree.GetCount() >= 1
        dialog.Hide()
        dialog.Destroy()
        pump(app)
