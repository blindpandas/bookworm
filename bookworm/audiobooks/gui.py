"""Native, keyboard-first audiobook shelf and player."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event

import wx

from bookworm import config, speech
from bookworm.paths import data_path

from .backend import MpvAudioBackend
from .exporter import (
    BITRATES,
    SAMPLE_RATES,
    ExportCancelledError,
    ExportOptions,
    export_book,
    save_copy,
)
from .importer import ImportCancelledError, import_book, relocate_book
from .metadata import TagDocument, save_tags
from .metadata_gui import FileInformationDialog, TagEditorDialog
from .model import format_time, parse_time
from .player import AudiobookPlayer, State
from .storage import AudioLibrary


def labeled_text(parent, sizer, label, value="", style=0):
    sizer.Add(wx.StaticText(parent, label=label), 0, wx.TOP, 8)
    control = wx.TextCtrl(parent, value=value, style=style, name=label)
    control.SetName(label)
    sizer.Add(control, 0, wx.EXPAND | wx.BOTTOM, 4)
    return control


class ImportPreview(wx.Dialog):
    def __init__(self, parent, book):
        super().__init__(
            parent,
            title=_("Review audiobook"),
            size=(650, 520),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.book = book
        self.chapters = list(book.chapters)
        box = wx.BoxSizer(wx.VERTICAL)
        self.title = labeled_text(self, box, _("Book title"), book.title)
        self.author = labeled_text(self, box, _("Author or narrator"), book.author)
        box.Add(wx.StaticText(self, label=_("Chapters in listening order")))
        self.list = wx.ListBox(self, name=_("Chapters in listening order"))
        box.Add(self.list, 1, wx.EXPAND)
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, delta in ((_("Move &up"), -1), (_("Move &down"), 1)):
            button = wx.Button(self, label=label)
            button.Bind(wx.EVT_BUTTON, lambda _event, d=delta: self.move(d))
            row.Add(button, 0, wx.ALL, 4)
        box.Add(row)
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(box, 1, wx.EXPAND | wx.ALL, 12)
        self.SetSizer(outer)
        self.refresh(0)
        self.Bind(wx.EVT_BUTTON, self.accept, id=wx.ID_OK)
        self.title.SetFocus()

    def refresh(self, selected):
        self.list.Set(
            [
                f"{i + 1}. {c.title} ({format_time(c.duration_ms)}) — {c.path}"
                for i, c in enumerate(self.chapters)
            ]
        )
        self.list.SetSelection(selected)

    def move(self, delta):
        index = self.list.GetSelection()
        target = index + delta
        if index != wx.NOT_FOUND and 0 <= target < len(self.chapters):
            self.chapters[index], self.chapters[target] = (
                self.chapters[target],
                self.chapters[index],
            )
            self.refresh(target)
            self.list.SetFocus()

    def accept(self, _event):
        if not self.title.Value.strip():
            wx.MessageBox(_("Please enter a book title."), _("Audiobooks"), parent=self)
            self.title.SetFocus()
            return
        self.book = replace(
            self.book,
            title=self.title.Value.strip(),
            author=self.author.Value.strip(),
            chapters=tuple(self.chapters),
        )
        self.EndModal(wx.ID_OK)


class BookmarkEditor(wx.Dialog):
    def __init__(self, parent, title="", note=""):
        super().__init__(
            parent,
            title=_("Audiobook bookmark"),
            size=(520, 340),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        box = wx.BoxSizer(wx.VERTICAL)
        self.title = labeled_text(self, box, _("Bookmark name"), title)
        self.note = labeled_text(self, box, _("Note"), note, wx.TE_MULTILINE)
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL, 10)
        self.SetSizer(box)
        self.title.SetFocus()


class BookmarksDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(
            parent,
            title=_("Audiobook bookmarks"),
            size=(650, 440),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.owner = parent
        self.target = None
        box = wx.BoxSizer(wx.VERTICAL)
        self.list = wx.ListBox(self, name=_("Bookmarks"))
        box.Add(self.list, 1, wx.EXPAND | wx.ALL, 10)
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, handler in (
            (_("&Go to"), self.go),
            (_("&Edit note"), self.edit),
            (_("&Delete"), self.remove),
        ):
            button = wx.Button(self, label=label)
            button.Bind(wx.EVT_BUTTON, handler)
            row.Add(button, 0, wx.ALL, 4)
        box.Add(row)
        box.Add(self.CreateButtonSizer(wx.CLOSE), 0, wx.ALL | wx.ALIGN_RIGHT, 10)
        self.SetSizer(box)
        self.Bind(wx.EVT_BUTTON, lambda _event: self.EndModal(wx.ID_CLOSE), id=wx.ID_CLOSE)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.go)
        self.refresh()
        self.list.SetFocus()

    def refresh(self):
        selected = max(0, self.list.GetSelection())
        self.items = self.owner.library.bookmarks(self.owner.player.book.id)
        self.list.Set(
            [f"{format_time(b['position'])} — {b['title']} — {b['note']}" for b in self.items]
        )
        if self.items:
            self.list.SetSelection(min(selected, len(self.items) - 1))

    def selected(self):
        index = self.list.GetSelection()
        return self.items[index] if index != wx.NOT_FOUND else None

    def go(self, _event):
        item = self.selected()
        if item:
            self.target = item["position"]
            self.EndModal(wx.ID_OK)

    def edit(self, _event):
        item = self.selected()
        if not item:
            return
        with BookmarkEditor(self, item["title"], item["note"]) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.owner.guarded(
                    lambda: self.owner.library.bookmark(
                        self.owner.player.book,
                        item["position"],
                        dialog.title.Value,
                        dialog.note.Value,
                        item["id"],
                    )
                )
                self.refresh()

    def remove(self, _event):
        item = self.selected()
        if (
            item
            and wx.MessageBox(
                _("Delete this bookmark and its note?"),
                _("Audiobooks"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            self.owner.guarded(lambda: self.owner.library.remove_bookmark(item["id"]))
            self.refresh()


class AudioSettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Audiobook settings"))
        box = wx.BoxSizer(wx.VERTICAL)
        self.controls = {}
        settings = config.conf["audiobooks"]
        for key, label, minimum, maximum in (
            ("short_skip_seconds", _("Short jump (seconds)"), 1, 60),
            ("long_skip_seconds", _("Long jump (seconds)"), 10, 600),
            ("resume_rewind_seconds", _("Rewind when reopening (seconds)"), 0, 30),
        ):
            box.Add(wx.StaticText(self, label=label), 0, wx.TOP, 8)
            control = wx.SpinCtrl(self, min=minimum, max=maximum, initial=settings[key], name=label)
            control.SetName(label)
            self.controls[key] = control
            box.Add(control, 0, wx.EXPAND)
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL, 12)
        self.SetSizerAndFit(box)
        self.Bind(wx.EVT_BUTTON, self.accept, id=wx.ID_OK)

    def accept(self, _event):
        if self.controls["long_skip_seconds"].Value <= self.controls["short_skip_seconds"].Value:
            wx.MessageBox(
                _("The long jump must be longer than the short jump."),
                _("Audiobooks"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            self.controls["long_skip_seconds"].SetFocus()
            return
        self.EndModal(wx.ID_OK)


class ExportDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Export audiobook"))
        box = wx.BoxSizer(wx.VERTICAL)
        self.formats = ("mp3", "m4b", "flac", "wav")
        self.format = self.choice(
            box,
            _("Audio format"),
            [
                _("MP3"),
                _("M4B (AAC audiobook)"),
                _("FLAC (lossless, 16-bit)"),
                _("WAV (uncompressed, 16-bit)"),
            ],
            0,
        )
        self.bitrate = self.choice(box, _("Bitrate (kbit/s)"), [str(x) for x in BITRATES], 2)
        self.sample_rate = self.choice(
            box, _("Sample rate (Hz)"), [str(x) for x in SAMPLE_RATES], 1
        )
        self.channels = self.choice(box, _("Channels"), [_("Mono"), _("Stereo")], 1)
        self.processed = wx.CheckBox(
            self, label=_("Apply the current playback speed and speech boost")
        )
        box.Add(self.processed, 0, wx.ALL, 8)
        self.details = labeled_text(
            self,
            box,
            _("Export information"),
            _(
                "The whole book is saved as one new file. Original recordings are kept. "
                "Playback volume is not applied. MP3 and M4B retain chapter titles; WAV and FLAC do not. "
                "Increasing bitrate or sample rate cannot restore lost quality."
            ),
            wx.TE_READONLY | wx.TE_MULTILINE,
        )
        self.details.SetMinSize((560, 100))
        box.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.ALL | wx.ALIGN_RIGHT, 12)
        self.SetSizerAndFit(box)
        self.format.Bind(wx.EVT_CHOICE, self.update_bitrate)
        self.sample_rate.Bind(wx.EVT_CHOICE, self.update_bitrate)
        self.Bind(wx.EVT_BUTTON, self.accept, id=wx.ID_OK)
        self.options = None

    def choice(self, box, label, choices, selection):
        box.Add(wx.StaticText(self, label=label), 0, wx.TOP, 8)
        control = wx.Choice(self, choices=choices, name=label)
        control.SetName(label)
        control.SetSelection(selection)
        box.Add(control, 0, wx.EXPAND)
        return control

    def update_bitrate(self, _event):
        self.bitrate.Enable(self.format.Selection < 2)

    def accept(self, _event):
        player = self.Parent.player
        try:
            self.options = ExportOptions(
                format=self.formats[self.format.Selection],
                bitrate=BITRATES[self.bitrate.Selection],
                sample_rate=SAMPLE_RATES[self.sample_rate.Selection],
                channels=self.channels.Selection + 1,
                rate=player.rate if self.processed.Value else 1,
                boost=player.boost if self.processed.Value else 0,
            )
        except ValueError as exc:
            wx.MessageBox(str(exc), _("Export audiobook"), wx.OK | wx.ICON_ERROR, self)
            return
        self.EndModal(wx.ID_OK)


class AudiobookWindow(wx.Frame):
    def __init__(self, parent, on_closed):  # noqa: PLR0915 - native control layout
        super().__init__(parent, title=_("Audiobooks — Bookworm"), size=(1000, 800))
        self.on_closed = on_closed
        self.closing = False
        self.library = AudioLibrary(
            data_path("audiobooks", "library.sqlite3"), defer_positions=True
        )
        self.player = AudiobookPlayer(
            MpvAudioBackend(wx.CallAfter),
            self.library,
            self.announce,
            error_notify=self.playback_error,
        )
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="audiobook-import")
        self.cancel_import = Event()
        self.importing = False
        self.exporting = False
        self.cancel_export = Event()
        self._last_export_progress = None
        self.loop_a = None
        self.last_chapter = None
        self._last_status = ""
        panel = wx.ScrolledWindow(self, style=wx.TAB_TRAVERSAL)
        panel.SetScrollRate(0, 20)
        box = wx.BoxSizer(wx.VERTICAL)
        self.search = labeled_text(panel, box, _("Search audiobooks"))
        self.books = wx.ListBox(panel, name=_("Audiobook shelf"))
        box.Add(self.books, 1, wx.EXPAND)
        self.activate_on_enter(self.books, self.open_selected)
        self.books.Bind(wx.EVT_LISTBOX_DCLICK, lambda _event: self.guarded(self.open_selected))
        self.search.Bind(wx.EVT_TEXT, lambda _event: self.refresh_books())
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, action in (
            (_("&Open selected book"), self.open_selected),
            (_("Add &file…"), self.add_file),
            (_("Add f&older…"), self.add_folder),
        ):
            self.button(panel, row, label, action)
        box.Add(row)
        box.Add(wx.StaticText(panel, label=_("Chapters")), 0, wx.TOP, 8)
        self.chapters = wx.ListBox(panel, name=_("Chapters"))
        self.activate_on_enter(self.chapters, self.go_chapter)
        self.chapters.Bind(wx.EVT_LISTBOX_DCLICK, lambda _event: self.guarded(self.go_chapter))
        box.Add(self.chapters, 1, wx.EXPAND)
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, action in (
            (_("Previous chapter"), lambda: self.player.chapter(-1)),
            (_("&Play / pause"), self.toggle),
            (_("&Stop"), self.stop),
            (_("Next chapter"), lambda: self.player.chapter(1)),
            (_("Go to selected chapter"), self.go_chapter),
        ):
            self.button(panel, row, label, action)
        box.Add(row)
        row = wx.WrapSizer(wx.HORIZONTAL)
        for label, long, direction in (
            (_("Back (short)"), False, -1),
            (_("Forward (short)"), False, 1),
            (_("Back (long)"), True, -1),
            (_("Forward (long)"), True, 1),
        ):
            self.button(
                panel,
                row,
                label,
                lambda longer=long, direction=direction: self.skip(direction, longer),
            )
        box.Add(row)
        row = wx.WrapSizer(wx.HORIZONTAL)
        row.Add(wx.StaticText(panel, label=_("Speed (%)")), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        self.speed = wx.SpinCtrl(panel, min=50, max=200, initial=100, name=_("Speed (%)"))
        self.speed.SetName(_("Speed (%)"))
        row.Add(self.speed)
        self.button(panel, row, _("Apply speed"), self.apply_speed)
        row.Add(
            wx.StaticText(panel, label=_("Volume (%)")), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4
        )
        self.volume = wx.Slider(
            panel,
            value=100,
            minValue=0,
            maxValue=100,
            style=wx.SL_HORIZONTAL | wx.SL_LABELS,
            name=_("Volume (%)"),
        )
        self.volume.SetName(_("Volume (%)"))
        self.volume.SetLineSize(5)
        self.volume.SetPageSize(10)
        self.volume.Bind(wx.EVT_SLIDER, lambda _event: self.guarded(self.apply_volume))
        row.Add(self.volume)
        self.button(panel, row, _("Apply volume"), self.apply_volume)
        box.Add(row)
        row = wx.WrapSizer(wx.HORIZONTAL)
        row.Add(
            wx.StaticText(panel, label=_("Speech boost (dB)")),
            0,
            wx.ALIGN_CENTER_VERTICAL | wx.ALL,
            4,
        )
        self.boost = wx.SpinCtrl(panel, min=0, max=12, initial=0, name=_("Speech boost (dB)"))
        self.boost.SetName(_("Speech boost (dB)"))
        row.Add(self.boost)
        self.button(panel, row, _("Apply speech boost"), self.apply_boost)
        self.button(panel, row, _("Reset speech boost"), lambda: self.change_boost(reset=True))
        box.Add(row)
        self.status = labeled_text(
            panel, box, _("Listening information"), style=wx.TE_READONLY | wx.TE_MULTILINE
        )
        self.import_status = wx.StaticText(panel, label="")
        box.Add(self.import_status)
        self.button(panel, box, _("Cancel import"), self.cancel_import.set)
        self.export_status = labeled_text(
            panel, box, _("File operation progress"), style=wx.TE_READONLY
        )
        self.button(panel, box, _("Cancel file operation"), self.cancel_export.set)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(box, 1, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(outer)
        panel.FitInside()
        area = wx.GetClientDisplayRect()
        self.SetSize((min(1000, area.width), min(800, area.height)))
        self.create_menus()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(100)
        self.refresh_books()
        self.books.SetFocus()

    def activate_on_enter(self, control, action):
        def key_handler(event):
            if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
                self.guarded(action)
            else:
                event.Skip()

        control.Bind(wx.EVT_KEY_DOWN, key_handler)

    def button(self, parent, box, label, action):
        button = wx.Button(parent, label=label)
        button.SetName(wx.StripMenuCodes(label))
        button.Bind(wx.EVT_BUTTON, lambda _event: self.guarded(action))
        box.Add(button, 0, wx.ALL, 3)
        return button

    def create_menus(self):
        bar = wx.MenuBar()
        groups = [
            (
                _("&Library"),
                [
                    (_("Open selected book\tCtrl+O"), self.open_selected),
                    (_("Add audio file…"), self.add_file),
                    (_("Add book folder…"), self.add_folder),
                    (_("Relocate selected book…"), self.relocate),
                    (_("Remove selected book…"), self.remove_book),
                    (_("Back up audiobook library…"), self.backup),
                    (_("Save original recordings as…"), self.save_original),
                    (_("Export audiobook…"), self.export_audio),
                    (_("Audiobook settings…"), self.settings),
                    (_("Close\tAlt+F4"), self.Close),
                ],
            ),
            (
                _("&Playback"),
                [
                    (_("Play / pause\tF5"), self.toggle),
                    (_("Pause\tF6"), self.player.pause),
                    (_("Stop\tF9"), self.stop),
                    (_("Back (short)\tF7"), lambda: self.skip(-1)),
                    (_("Forward (short)\tF8"), lambda: self.skip(1)),
                    (_("Back (long)\tShift+F7"), lambda: self.skip(-1, True)),
                    (_("Forward (long)\tShift+F8"), lambda: self.skip(1, True)),
                    (_("Previous chapter\tCtrl+PageUp"), lambda: self.player.chapter(-1)),
                    (_("Next chapter\tCtrl+PageDown"), lambda: self.player.chapter(1)),
                    (_("Go to time…\tCtrl+G"), self.go_time),
                    (_("Slower\tAlt+Down"), lambda: self.change_speed(-0.05)),
                    (_("Faster\tAlt+Up"), lambda: self.change_speed(0.05)),
                    (_("Normal speed\tCtrl+0"), lambda: self.change_speed(reset=True)),
                    (_("Volume down\tAlt+PageDown"), lambda: self.change_volume(-0.05)),
                    (_("Volume up\tAlt+PageUp"), lambda: self.change_volume(0.05)),
                    (_("Less speech boost\tAlt+Home"), lambda: self.change_boost(-1)),
                    (_("More speech boost\tAlt+End"), lambda: self.change_boost(1)),
                    (_("Listening information\tCtrl+I"), self.information),
                    (_("Detailed listening times…\tCtrl+F12"), self.detailed_times),
                    (_("Audio file information…\tCtrl+Shift+I"), lambda: self.open_metadata(False)),
                    (_("Edit audio tags…\tCtrl+Shift+T"), lambda: self.open_metadata(True)),
                    (_("Sleep timer…"), self.sleep_timer),
                    (_("Sleep at end of chapter"), self.sleep_at_chapter),
                    (_("Cancel sleep timer"), self.player.set_sleep),
                    (_("Set repeat start (A)"), self.set_loop_a),
                    (_("Set repeat end (B)"), self.set_loop_b),
                    (_("Cancel repeat"), self.player.set_loop),
                ],
            ),
            (
                _("&Bookmarks"),
                [
                    (_("Add bookmark…\tCtrl+B"), self.add_bookmark),
                    (_("Browse bookmarks…\tCtrl+Shift+B"), self.browse_bookmarks),
                    (_("Export bookmarks…"), self.export_bookmarks),
                    (_("Import bookmarks…"), self.import_bookmarks),
                ],
            ),
        ]
        groups.append((_("&Help"), [(_("Audiobook help\tF1"), self.help)]))
        self.shortcut_index = {}
        accelerators = []
        for label, actions in groups:
            menu = wx.Menu()
            for text, action in actions:
                item = menu.Append(wx.ID_ANY, text)
                accelerator = item.GetAccel()
                if accelerator:
                    combination = (accelerator.GetFlags(), accelerator.GetKeyCode())
                    if combination in self.shortcut_index:
                        raise ValueError(
                            _("Duplicate audiobook keyboard shortcut: {shortcut}").format(
                                shortcut=text
                            )
                        )
                    self.shortcut_index[combination] = text
                    accelerators.append((*combination, item.GetId()))
                self.Bind(wx.EVT_MENU, lambda _event, a=action: self.guarded(a), item)
            bar.Append(menu, label)
        self.SetMenuBar(bar)
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerators))

    def help(self):
        from bookworm import app
        from bookworm.paths import userguide_path

        self.player.pause()
        guide = userguide_path(app.current_language.pylang, "bookworm.html")
        wx.LaunchDefaultBrowser(guide.resolve().as_uri() + "#audiobooks")

    def guarded(self, action):
        try:
            return action()
        except Exception as exc:
            writer = self.library.position_writer
            if writer is not None and writer.error is exc:
                self.player._fail(
                    _("The listening position could not be saved: {reason}").format(reason=exc)
                )
            else:
                wx.MessageBox(str(exc), _("Audiobooks"), wx.OK | wx.ICON_ERROR, self)
            return None

    def announce(self, message):
        if not self.closing:
            self.status.ChangeValue(message)
            if wx.Window.FindFocus() is not self.status:
                speech.announce(message)

    def playback_error(self, message):
        if not self.closing:
            self.status.ChangeValue(message)
            # Native dialog focus supplies its one accessible announcement.
            # Do not call speech.announce for the same error.
            wx.MessageBox(message, _("Audio playback error"), wx.OK | wx.ICON_ERROR, self)

    def refresh_books(self):
        previous = self.selected_book()
        query = self.search.Value.casefold()
        self.visible_books = [
            b for b in self.library.books() if query in f"{b.title} {b.author}".casefold()
        ]
        labels = []
        for book in self.visible_books:
            state = self.library.state(book.id)
            status = (
                _("Finished")
                if state["completed"]
                else f"{state['position'] / book.duration_ms:.0%}"
            )
            labels.append(f"{book.title} — {book.author} — {status}")
        self.books.Set(labels)
        if labels:
            selected = next(
                (i for i, b in enumerate(self.visible_books) if previous and b.id == previous.id), 0
            )
            self.books.SetSelection(selected)

    def selected_book(self):
        index = self.books.GetSelection()
        books = getattr(self, "visible_books", [])
        return books[index] if 0 <= index < len(books) else None

    def require_book(self):
        if self.player.book is None:
            raise ValueError(_("Open an audiobook first."))
        return self.player.book

    def open_selected(self):
        book = self.selected_book()
        if book is None:
            return
        self.stop_tts()
        self.player.open(book, config.conf["audiobooks"]["resume_rewind_seconds"] * 1000)
        self.chapters.Set(
            [
                f"{i + 1}. {c.title} — {format_time(c.duration_ms)}"
                for i, c in enumerate(book.chapters)
            ]
        )
        self.chapters.SetSelection(self.player.chapter_index)
        self.speed.Value = round(self.player.rate * 100)
        self.volume.Value = round(self.player.volume * 100)
        self.boost.Value = round(self.player.boost)
        self.SetTitle(_("{title} — Audiobooks — Bookworm").format(title=book.title))
        self.loop_a = None
        self.last_chapter = self.player.chapter_index
        self.information()

    def stop_tts(self):
        handler = getattr(wx.GetApp(), "service_handler", None)
        audio = handler.get_service("audiobooks") if handler else None
        if audio:
            audio.media_active = True
        tts = handler.get_service("text_to_speech") if handler else None
        if tts and tts.engine is not None:
            tts.stop_speech(user_requested=True)

    def toggle(self):
        if self.player.book is None:
            self.open_selected()
        self.require_book()
        self.stop_tts()
        self.player.toggle()
        if self.player.state is State.ERROR:
            return
        self.announce(
            _("Loading audio")
            if self.player.state is State.LOADING
            else (_("Playing") if self.player.desired_play else _("Paused"))
        )

    def stop(self):
        self.require_book()
        self.player.stop()
        self.loop_a = None
        self.announce(_("Stopped"))

    def skip(self, direction, long=False):
        self.require_book()
        seconds = config.conf["audiobooks"]["long_skip_seconds" if long else "short_skip_seconds"]
        self.player.skip(direction * seconds * 1000)

    def go_chapter(self):
        book = self.require_book()
        index = self.chapters.GetSelection()
        if index != wx.NOT_FOUND:
            self.player.seek(book.offsets[index])

    def go_time(self):
        book = self.require_book()
        with wx.TextEntryDialog(
            self,
            _(
                "Time from the beginning of the book (hh:mm:ss, mm:ss or seconds; decimals are allowed)"
            ),
            _("Go to time"),
            format_time(self.player.position_ms, include_milliseconds=True),
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                target = parse_time(dialog.Value)
                if target > book.duration_ms:
                    raise ValueError(_("That time is beyond the end of this book."))
                self.player.seek(target)

    def change_speed(self, delta=0, reset=False):
        self.require_book()
        rate = 1 if reset else round(max(0.5, min(2, self.player.rate + delta)), 2)
        self.player.set_rate(rate)
        self.speed.Value = round(rate * 100)
        self.announce_value(
            self.speed, _("Playback speed: {percent}%").format(percent=round(rate * 100))
        )

    def apply_speed(self):
        self.require_book()
        self.player.set_rate(self.speed.Value / 100)

    def apply_boost(self):
        self.require_book()
        self.player.set_boost(self.boost.Value)
        # The native spin control already exposes the edited value.

    def change_boost(self, delta=0, reset=False):
        self.require_book()
        boost = 0 if reset else max(0, min(12, self.player.boost + delta))
        self.player.set_boost(boost)
        self.boost.Value = round(boost)
        self.announce_value(self.boost, _("Speech boost: {boost} dB").format(boost=boost))

    def announce_value(self, control, message):
        focus = wx.Window.FindFocus()
        if focus is not control and (focus is None or not control.IsDescendant(focus)):
            self.announce(message)

    def apply_volume(self):
        self.require_book()
        self.player.set_volume(self.volume.Value / 100)
        # No speech here: MSAA/UIA announces the native slider value once.

    def change_volume(self, delta):
        self.require_book()
        volume = round(max(0, min(1, self.player.volume + delta)), 2)
        self.player.set_volume(volume)
        self.volume.Value = round(volume * 100)
        self.announce_value(
            self.volume, _("Volume: {percent}%").format(percent=round(volume * 100))
        )

    def information(self):
        book = self.require_book()
        self.player.poll(advance=False)
        index = self.player.chapter_index
        chapter = book.chapters[index]
        file_position = chapter.start_ms + self.player.position_ms - book.offsets[index]
        file_duration = max(c.end_ms for c in book.chapters if c.path == chapter.path)
        remaining = (book.duration_ms - self.player.position_ms) / self.player.rate
        message = _(
            "{title}. Chapter {chapter} of {count}: {name}. "
            "File position {file_position} of {file_duration}; remaining {file_remaining}. "
            "Book position {position} of {duration}. "
            "Remaining listening time at {percent}%: {remaining}."
        ).format(
            title=book.title,
            chapter=index + 1,
            count=len(book.chapters),
            name=book.chapters[index].title,
            file_position=format_time(file_position),
            file_duration=format_time(file_duration),
            file_remaining=format_time(max(0, file_duration - file_position)),
            position=format_time(self.player.position_ms),
            duration=format_time(book.duration_ms),
            percent=round(self.player.rate * 100),
            remaining=format_time(remaining),
        )
        self.announce(message)

    def detailed_times(self):
        with wx.Dialog(
            self,
            title=_("Detailed listening times"),
            size=(700, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        ) as dialog:
            box = wx.BoxSizer(wx.VERTICAL)
            text = wx.TextCtrl(
                dialog,
                value=self.time_report(),
                style=wx.TE_READONLY | wx.TE_MULTILINE,
                name=_("Detailed listening times"),
            )
            text.SetName(_("Detailed listening times"))
            box.Add(text, 1, wx.EXPAND | wx.ALL, 12)
            live = wx.CheckBox(dialog, label=_("Update times automatically"))
            live.Value = True
            box.Add(live, 0, wx.ALL, 8)
            box.Add(dialog.CreateButtonSizer(wx.OK), 0, wx.ALL | wx.ALIGN_RIGHT, 12)
            dialog.SetSizer(box)
            timer = wx.Timer(dialog)

            def update(_event):
                if not live.Value or self.player.book is None:
                    return
                value = self.time_report()
                if value != text.Value:
                    selection = text.GetSelection()
                    text.ChangeValue(value)
                    text.SetSelection(min(selection[0], len(value)), min(selection[1], len(value)))

            dialog.Bind(wx.EVT_TIMER, update, timer)
            timer.Start(1000)
            text.SetInsertionPoint(0)
            text.SetFocus()
            try:
                dialog.ShowModal()
            finally:
                timer.Stop()

    def time_report(self):
        book = self.require_book()
        self.player.poll(advance=False)
        index = self.player.chapter_index
        chapter = book.chapters[index]
        position = self.player.position_ms
        chapter_position = position - book.offsets[index]
        file_position = chapter.start_ms + chapter_position
        file_duration = max(c.end_ms for c in book.chapters if c.path == chapter.path)
        files = list(dict.fromkeys(c.path for c in book.chapters))

        def precise(milliseconds):
            milliseconds = max(0, round(milliseconds))
            return format_time(milliseconds) + f".{milliseconds % 1000:03d}"

        rows = [
            (_("Book title"), book.title),
            (_("File"), chapter.path),
            (
                _("File number"),
                _("{current} of {total}").format(
                    current=files.index(chapter.path) + 1, total=len(files)
                ),
            ),
            (_("File position"), precise(file_position)),
            (_("File duration"), precise(file_duration)),
            (_("File time remaining"), precise(file_duration - file_position)),
            (
                _("File listening time remaining at the current speed"),
                precise((file_duration - file_position) / self.player.rate),
            ),
            (_("Chapter"), chapter.title),
            (_("Chapter position"), precise(chapter_position)),
            (_("Chapter duration"), precise(chapter.duration_ms)),
            (_("Chapter time remaining"), precise(chapter.duration_ms - chapter_position)),
            (_("Book position"), precise(position)),
            (_("Book duration"), precise(book.duration_ms)),
            (_("Book time remaining"), precise(book.duration_ms - position)),
            (
                _("Book listening time remaining at the current speed"),
                precise((book.duration_ms - position) / self.player.rate),
            ),
            (_("Speed (%)"), str(round(self.player.rate * 100))),
            (_("Volume (%)"), str(round(self.player.volume * 100))),
            (_("Speech boost (dB)"), str(self.player.boost)),
            (
                _("Times"),
                _(
                    "Remaining listening time excludes pauses and section repeats. Disable automatic updates to read a fixed snapshot."
                ),
            ),
        ]
        return "\n".join(f"{label}: {value}" for label, value in rows)

    def open_metadata(self, edit):
        self.require_worker_idle()
        book = self.require_book()
        path = book.absolute_path(self.player.chapter_index)
        if edit:
            self.player.pause()
        self.exporting = True
        future = self.worker.submit(TagDocument.read, path)
        future.add_done_callback(lambda f: wx.CallAfter(self.show_metadata, f, edit))

    def show_metadata(self, future, edit):
        if self.closing:
            return
        self.exporting = False
        try:
            document = future.result()
            if not edit:
                with FileInformationDialog(self, document) as dialog:
                    dialog.ShowModal()
                return
            with TagEditorDialog(self, document) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                version = 3 + dialog.version.Selection if dialog.version else None
                v1 = dialog.v1
            self.player.close()
            self.cancel_export.clear()
            self.exporting = True
            future = self.worker.submit(
                save_tags,
                document,
                self.cancel_export,
                v2_version=version,
                v1=v1,
                library_path=data_path("audiobooks", "library.sqlite3"),
            )
            future.add_done_callback(lambda f: wx.CallAfter(self.finish_tags, f))
        except Exception as exc:
            wx.MessageBox(str(exc), _("Audio file information"), wx.OK | wx.ICON_ERROR, self)

    def finish_tags(self, future):
        if self.closing:
            return
        self.exporting = False
        try:
            result = future.result()
            self.refresh_books()
            self.chapters.Clear()
            self.announce(
                _("Tags saved and audio verified. Backup: {path}").format(path=result["backup"])
            )
        except ExportCancelledError:
            self.announce(_("Tag editing cancelled. The original file has been kept."))
        except Exception as exc:
            wx.MessageBox(str(exc), _("Edit audio tags"), wx.OK | wx.ICON_ERROR, self)

    def on_timer(self, _event):
        if self.closing:
            return
        try:
            self.player.poll()
        except Exception as exc:
            self.player._fail(exc)
        book = self.player.book
        if book:
            chapter = self.player.chapter_index
            self.last_chapter = chapter
            # Chapter changes do not speak over the narrator. Native chapter
            # list navigation and Ctrl+I expose the same information on demand.
            if self.player.state in (State.ERROR, State.LOADING):
                return
            text = _("Position {position} of {duration}; speed {percent}%").format(
                position=format_time(self.player.position_ms),
                duration=format_time(book.duration_ms),
                percent=round(self.player.rate * 100),
            )
            if text != self._last_status and wx.Window.FindFocus() is not self.status:
                self.status.ChangeValue(text)
                self._last_status = text

    def add_file(self):
        with wx.FileDialog(
            self,
            _("Add an audiobook file"),
            wildcard=_("Audio files") + "|*.mp3;*.m4b;*.m4a;*.wav;*.flac;*.ogg;*.opus",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.begin_import(dialog.Path)

    def add_folder(self):
        with wx.DirDialog(self, _("Select the folder containing one audiobook")) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.begin_import(dialog.Path)

    def begin_import(self, path):
        self.require_worker_idle()
        self.cancel_import.clear()
        self.importing = True

        def progress(current, total, name):
            wx.CallAfter(self.show_import_progress, current, total, name)

        future = self.worker.submit(import_book, path, self.cancel_import, progress, verify=True)
        future.add_done_callback(lambda f: wx.CallAfter(self.finish_import, f))

    def show_import_progress(self, current, total, name):
        if not self.closing:
            self.import_status.SetLabel(
                _("Importing {current} of {total}: {file}").format(
                    current=current, total=total, file=name
                )
            )

    def finish_import(self, future):
        if self.closing:
            return
        self.importing = False
        self.import_status.SetLabel("")
        try:
            book = future.result()
            with ImportPreview(self, book) as dialog:
                if dialog.ShowModal() == wx.ID_OK:
                    self.library.add(dialog.book)
                    self.search.ChangeValue("")
                    self.refresh_books()
                    self.announce(_("Audiobook added."))
        except ImportCancelledError:
            self.announce(_("Import cancelled."))
        except Exception as exc:
            wx.MessageBox(str(exc), _("Audiobooks"), wx.OK | wx.ICON_ERROR, self)

    def relocate(self):
        self.require_worker_idle()
        book = self.selected_book()
        if not book:
            return
        with wx.DirDialog(self, _("Select the book's new folder")) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.exporting = True
                self.cancel_export.clear()
                future = self.worker.submit(relocate_book, book, dialog.Path, self.cancel_export)
                future.add_done_callback(lambda f: wx.CallAfter(self.finish_relocation, f))

    def finish_relocation(self, future):
        if self.closing:
            return
        self.exporting = False
        try:
            relocated = future.result()
            if self.player.book and self.player.book.id == relocated.id:
                self.player.close()
                self.player.open(relocated, 0)
            self.library.update_manifest(relocated)
            self.refresh_books()
            self.announce(_("The audiobook folder has been updated."))
        except ImportCancelledError:
            self.announce(_("File operation cancelled. No completed file was replaced."))
        except Exception as exc:
            wx.MessageBox(str(exc), _("Audiobooks"), wx.OK | wx.ICON_ERROR, self)

    def remove_book(self):
        book = self.selected_book()
        if not book:
            return
        if (
            wx.MessageBox(
                _(
                    "Remove this audiobook, its saved position and bookmarks from the shelf? "
                    "The audio files will be kept."
                ),
                _("Audiobooks"),
                wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
                self,
            )
            == wx.YES
        ):
            if self.player.book and self.player.book.id == book.id:
                self.player.close()
                self.chapters.Clear()
            self.library.remove(book.id)
            self.refresh_books()

    def settings(self):
        with AudioSettingsDialog(self) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                if (
                    dialog.controls["long_skip_seconds"].Value
                    <= dialog.controls["short_skip_seconds"].Value
                ):
                    raise ValueError(_("The long jump must be longer than the short jump."))
                for key, control in dialog.controls.items():
                    config.conf["audiobooks"][key] = control.Value
                config.save()

    def sleep_timer(self):
        self.require_book()
        with wx.NumberEntryDialog(
            self, _("Use 0 to cancel the timer."), _("Minutes"), _("Sleep timer"), 30, 0, 1440
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.player.set_sleep(dialog.Value)

    def sleep_at_chapter(self):
        self.require_book()
        self.player.set_sleep(end_of_chapter=True)
        self.announce(_("Playback will pause at the end of this chapter."))

    def set_loop_a(self):
        self.require_book()
        self.player.poll(advance=False)
        self.loop_a = self.player.position_ms
        self.announce(_("Repeat start set."))

    def set_loop_b(self):
        self.require_book()
        self.player.poll(advance=False)
        if self.loop_a is None:
            raise ValueError(_("Set the repeat start first."))
        self.player.set_loop(self.loop_a, self.player.position_ms)
        self.announce(_("Section repeat enabled."))

    def add_bookmark(self):
        book = self.require_book()
        self.player.poll(advance=False)
        position = self.player.position_ms
        with BookmarkEditor(self, format_time(position)) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.library.bookmark(book, position, dialog.title.Value, dialog.note.Value)
                self.announce(_("Bookmark added."))

    def browse_bookmarks(self):
        self.require_book()
        with BookmarksDialog(self) as dialog:
            if dialog.ShowModal() == wx.ID_OK and dialog.target is not None:
                self.player.seek(dialog.target)

    def export_bookmarks(self):
        book = self.require_book()
        with wx.FileDialog(
            self,
            _("Export audiobook bookmarks"),
            defaultFile="bookmarks.json",
            wildcard="JSON|*.json",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                path = Path(dialog.Path)
                if path.suffix.casefold() != ".json":
                    raise ValueError(_("Use the .json extension for audiobook bookmarks."))
                from .metadata_gui import atomic_write

                atomic_write(path, self.library.export_bookmarks(book).encode("utf-8"))

    def import_bookmarks(self):
        book = self.require_book()
        with wx.FileDialog(
            self,
            _("Import audiobook bookmarks"),
            wildcard="JSON|*.json",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                path = Path(dialog.Path)
                if path.stat().st_size > 10 * 1024 * 1024:
                    raise ValueError(_("The bookmark file is too large."))
                count = self.library.import_bookmarks(book, path.read_text(encoding="utf-8"))
                self.announce(_("Imported bookmarks: {count}").format(count=count))

    def backup(self):
        self.player.checkpoint()
        with wx.FileDialog(
            self,
            _("Back up audiobook library"),
            defaultFile="audiobooks.sqlite3",
            wildcard="SQLite|*.sqlite3",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                if (
                    Path(dialog.Path).resolve()
                    == data_path("audiobooks", "library.sqlite3").resolve()
                ):
                    raise ValueError(_("Choose a different file for the backup."))
                self.library.backup(dialog.Path)

    def require_worker_idle(self):
        if self.importing or self.exporting:
            raise ValueError(
                _("A file operation is already in progress. Wait for it to finish or cancel it.")
            )

    def save_original(self):
        book = self.require_book()
        self.require_worker_idle()
        paths = list(dict.fromkeys(c.path for c in book.chapters))
        if len(paths) == 1:
            source = Path(paths[0])
            with wx.FileDialog(
                self,
                _("Save original recording as"),
                defaultFile=source.name,
                wildcard=_("Original audio format") + "|*" + source.suffix,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as dialog:
                if dialog.ShowModal() == wx.ID_OK:
                    self.begin_export(save_copy, book, dialog.Path, overwrite=True)
        else:
            with wx.DirDialog(
                self, _("Choose the parent folder for the copy"), style=wx.DD_DIR_MUST_EXIST
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                parent = Path(dialog.Path)
            with wx.TextEntryDialog(
                self, _("New folder name"), _("Save original recordings"), "Audiobook"
            ) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                name = dialog.Value.strip()
                if not name or name in (".", "..") or any(c in name for c in '<>:"/\\|?*'):
                    raise ValueError(_("Please enter a valid folder name."))
                self.begin_export(save_copy, book, parent / name)

    def export_audio(self):
        book = self.require_book()
        self.require_worker_idle()
        with ExportDialog(self) as options_dialog:
            if options_dialog.ShowModal() != wx.ID_OK:
                return
            options = options_dialog.options
        with wx.FileDialog(
            self,
            _("Export audiobook"),
            defaultFile="Audiobook." + options.format,
            wildcard=options.format.upper() + "|*." + options.format,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                self.begin_export(export_book, book, dialog.Path, options=options, overwrite=True)

    def begin_export(self, action, book, target, **kwargs):
        self.require_worker_idle()
        self.cancel_export.clear()
        self.exporting = True
        self._last_export_progress = None
        self.export_status.ChangeValue(_("Preparing file operation"))

        def progress(stage, percent):
            # Integer changes only: do not flood the GUI event queue, and never
            # send unsolicited speech while another control is being operated.
            value = (stage, percent)
            if value != self._last_export_progress:
                self._last_export_progress = value
                wx.CallAfter(self.show_export_progress, stage, percent)

        future = self.worker.submit(
            action, book, target, cancel=self.cancel_export, progress=progress, **kwargs
        )
        future.add_done_callback(lambda f: wx.CallAfter(self.finish_export, f))

    def show_export_progress(self, stage, percent):
        if not self.closing:
            self.export_status.ChangeValue(
                _("{stage}: {percent}%").format(stage=stage, percent=percent)
            )

    def finish_export(self, future):
        if self.closing:
            return
        self.exporting = False
        try:
            path = future.result()
            message = _("Saved and verified: {path}").format(path=path)
        except ExportCancelledError:
            message = _("File operation cancelled. No completed file was replaced.")
        except Exception as exc:
            self.export_status.ChangeValue(str(exc))
            wx.MessageBox(str(exc), _("Audiobooks"), wx.OK | wx.ICON_ERROR, self)
            return
        self.export_status.ChangeValue(message)
        self.announce_value(self.export_status, message)

    def on_close(self, event):
        if self.closing:
            event.Skip()
            return
        discard_positions = False
        try:
            self.player.close()
        except Exception as exc:
            if event.CanVeto():
                answer = wx.MessageBox(
                    _(
                        "The latest listening position could not be saved. Close anyway?\n{reason}"
                    ).format(reason=exc),
                    _("The listening position could not be saved"),
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING,
                    self,
                )
                if answer != wx.YES:
                    event.Veto()
                    return
            self.player.close(save=False)
            discard_positions = True
        self.closing = True
        self.timer.Stop()
        self.cancel_import.set()
        self.cancel_export.set()
        self.worker.shutdown(wait=False, cancel_futures=True)
        self.library.close(discard_positions=discard_positions)
        self.on_closed()
        self.Destroy()
