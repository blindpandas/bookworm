"""GUI-thread player state machine; native events are guarded by load generations."""

import math
import time
from enum import Enum

from .importer import check_audio_file


class State(Enum):
    EMPTY = "empty"
    LOADING = "loading"
    PAUSED = "paused"
    STOPPED = "stopped"
    PLAYING = "playing"
    FINISHED = "finished"
    ERROR = "error"


class AudiobookPlayer:
    def __init__(
        self,
        backend,
        library,
        notify=lambda _message: None,
        clock=time.monotonic,
        error_notify=None,
    ):
        self.backend = backend
        self.library = library
        self.notify = notify
        self.error_notify = error_notify or notify
        self.clock = clock
        self.book = None
        self.state = State.EMPTY
        self.position_ms = 0
        self.chapter_index = 0
        self.rate = self.volume = 1.0
        self.boost = 0
        self.completed = False
        self.generation = 0
        self.desired_play = False
        self._ready = False
        self._loaded_at = self._saved_at = clock()
        self.sleep_deadline = self.sleep_boundary = None
        self.loop_start = self.loop_end = None
        self.error = ""
        self._progress_at = clock()
        self._progress_position = None

    def open(self, book, rewind_ms=0):
        self.close()
        stored = self.library.state(book.id)
        self.book = book
        self.rate, self.volume = stored["rate"], stored["volume"]
        self.boost = stored["boost"]
        self.completed = bool(stored["completed"])
        position = max(0, stored["position"] - (0 if self.completed else rewind_ms))
        self._seek(position, play=False)

    def _fail(self, error):
        self.generation += 1
        self.desired_play = False
        self._ready = False
        self.state = State.ERROR
        self.error = str(error)
        try:
            self.backend.close()
        finally:
            self.error_notify(self.error)

    def _save(self):
        if self.book is not None:
            self.library.save_position(
                self.book, self.position_ms, self.rate, self.volume, self.completed, self.boost
            )
            self._saved_at = self.clock()

    def checkpoint(self):
        self.poll()
        try:
            self._save()
            self.library.flush_positions()
        except Exception as exc:
            self._fail(_("The listening position could not be saved: {reason}").format(reason=exc))
            raise

    def close(self, save=True):
        if self.book is not None and save:
            # Prevent a queued end event from advancing while shutting down.
            self.poll(advance=False)
            if self._ready:
                self.backend.pause()
                self.state = State.PAUSED
                self.desired_play = False
            self._save()
            self.library.flush_positions()
        self.generation += 1
        self.backend.close()
        self.book = None
        self.state = State.EMPTY
        self._ready = self.desired_play = False
        self.sleep_deadline = self.sleep_boundary = None
        self.loop_start = self.loop_end = None

    def _seek(self, position_ms, play):
        if self.book is None:
            return
        position_ms = max(0, min(int(position_ms), self.book.duration_ms))
        if position_ms >= self.book.duration_ms:
            self.backend.close()
            self.generation += 1
            self._ready = self.desired_play = False
            self.position_ms = self.book.duration_ms
            self.chapter_index = len(self.book.chapters) - 1
            self.state = State.FINISHED
            self.completed = True
            self._save()
            return
        index, file_position = self.book.locate(position_ms)
        self._progress_at, self._progress_position = self.clock(), None
        self.error = ""
        if (
            self._ready
            and self.book.chapters[index].path == self.book.chapters[self.chapter_index].path
        ):
            # A jump within an open recording is a native seek, not a teardown
            # and decoder reload. Keep its callbacks and desired play state.
            if not self.backend.seek(file_position):
                self._fail(_("The requested listening position could not be reached."))
                return
            self.position_ms, self.chapter_index = position_ms, index
            self.completed = False
            self.desired_play = play
            if play:
                self.play()
            else:
                self.backend.pause()
                self.state = State.PAUSED
            return
        self.generation += 1
        generation = self.generation
        self.backend.close()
        self._ready = False
        self.desired_play = play
        self.state = State.LOADING
        self.position_ms, self.chapter_index = position_ms, index
        self.completed = False
        self._loaded_at = self.clock()
        try:
            path = self.book.absolute_path(index)
            stat = check_audio_file(path)
            chapter = self.book.chapters[index]
            if stat.st_size != chapter.size or (
                chapter.mtime_ns and stat.st_mtime_ns != chapter.mtime_ns
            ):
                raise ValueError(_("The recording has changed. Import it as a new book."))
            self.backend.load(
                path,
                lambda: self._native_event(self._on_loaded, generation, file_position),
                lambda: self._native_event(self._on_finished, generation),
                lambda error: self._on_error(generation, error),
                rate=self.rate,
                volume=self.volume,
                boost=self.boost,
            )
        except Exception as exc:
            self._fail(_("Cannot play this recording: {reason}").format(reason=exc))

    def _native_event(self, callback, *args):
        try:
            callback(*args)
        except Exception as exc:
            self._fail(exc)

    def _on_error(self, generation, error):
        if generation == self.generation:
            self._fail(error)

    def _on_loaded(self, generation, file_position):
        if generation != self.generation or self.state is not State.LOADING:
            return
        try:
            if not self.backend.set_volume(self.volume):
                raise RuntimeError(_("The audio volume could not be set."))
            if not self.backend.set_boost(self.boost):
                raise RuntimeError(_("Speech boost could not be enabled safely."))
            if not self.backend.set_rate(self.rate):
                self.rate = 1.0
                self.notify(
                    _("This recording does not support the selected speed. Normal speed is used.")
                )
            if not self.backend.seek(file_position):
                raise RuntimeError(_("The requested listening position could not be reached."))
            self._ready = True
            self.state = State.PAUSED
            if self.desired_play:
                self.play()
        except Exception as exc:
            self._fail(exc)

    def _on_finished(self, generation):
        if generation != self.generation or self.state not in (State.PLAYING, State.PAUSED):
            return
        play = self.desired_play
        index = self.chapter_index
        while self._contiguous(index):
            index += 1
        boundary = self.book.offsets[index + 1]
        sleep_boundary = self.sleep_boundary
        if self._sleep_due(boundary):
            self._ready = False
            self._seek(
                min(boundary, sleep_boundary) if sleep_boundary is not None else boundary,
                play=False,
            )
            return
        self._ready = False  # The physical stream has ended; it must be reopened.
        if self.loop_end is not None and self.loop_end <= boundary:
            self._seek(self.loop_start, play=play)
        else:
            self._seek(boundary, play=play)
        self._save()

    def play(self):
        if self.book is None:
            return
        if self.state is State.FINISHED:
            self.notify(_("The audiobook is finished. Select a chapter to listen again."))
            return
        if self.state in (State.ERROR, State.STOPPED):
            self._seek(self.position_ms, play=True)
            return
        self.desired_play = True
        if self.state is State.LOADING:
            return
        if self.backend.play():
            self.state = State.PLAYING
            self._progress_at, self._progress_position = self.clock(), None
        else:
            self._fail(_("Playback could not be started."))

    def pause(self):
        self.desired_play = False
        if self.state is State.LOADING:
            return
        self.poll(advance=False)
        if self.state is State.PLAYING:
            if not self.backend.pause():
                self._fail(_("Playback could not be paused."))
            else:
                self.state = State.PAUSED
        self._save()

    def toggle(self):
        if self.desired_play or self.state is State.PLAYING:
            self.pause()
        else:
            self.play()

    def stop(self):
        if self.book is None:
            return
        # Invalidate callbacks before closing the decoder. Stop also resets a
        # finished or still-loading book; stale EOF/load events cannot undo it.
        self.generation += 1
        self.desired_play = self._ready = False
        self.sleep_deadline = self.sleep_boundary = None
        self.loop_start = self.loop_end = None
        self.backend.close()
        self.position_ms = self.chapter_index = 0
        self.completed = False
        self.error = ""
        self.state = State.STOPPED
        self._save()

    def seek(self, position_ms):
        play = self.desired_play
        self.poll(advance=False)
        self._seek(position_ms, play)
        self._save()

    def skip(self, delta_ms):
        self.poll(advance=False)
        self.seek(self.position_ms + delta_ms)

    def chapter(self, delta):
        if self.book is None:
            return
        index = max(0, min(self.chapter_index + delta, len(self.book.chapters) - 1))
        self.seek(self.book.offsets[index])

    def set_rate(self, rate):
        if not math.isfinite(rate) or not 0.5 <= rate <= 2:
            raise ValueError(_("Playback speed must be between 50% and 200%."))
        if self._ready and not self.backend.set_rate(rate):
            raise ValueError(_("This recording or audio backend does not support that speed."))
        self.rate = rate
        self._save()

    def set_volume(self, volume):
        if not math.isfinite(volume) or not 0 <= volume <= 1:
            raise ValueError("Invalid volume")
        if self._ready and not self.backend.set_volume(volume):
            raise ValueError(_("The audio volume could not be set."))
        self.volume = volume
        self._save()

    def set_boost(self, boost):
        if not math.isfinite(boost) or not 0 <= boost <= 12:
            raise ValueError(_("Speech boost must be between 0 and 12 dB."))
        if self._ready and not self.backend.set_boost(boost):
            raise ValueError(_("Speech boost could not be enabled safely."))
        self.boost = boost
        self._save()

    def set_sleep(self, minutes=0, end_of_chapter=False):
        if not 0 <= minutes <= 1440:
            raise ValueError("Invalid sleep interval")
        self.sleep_deadline = self.clock() + minutes * 60 if minutes else None
        self.sleep_boundary = (
            self.book.offsets[self.chapter_index + 1] if end_of_chapter and self.book else None
        )

    def _sleep_due(self, position):
        if (self.sleep_deadline is not None and self.clock() >= self.sleep_deadline) or (
            self.sleep_boundary is not None and position >= self.sleep_boundary
        ):
            self.sleep_deadline = self.sleep_boundary = None
            self.notify(_("Sleep timer finished. Playback paused."))
            return True
        return False

    def set_loop(self, start=None, end=None):
        if start is None:
            self.loop_start = self.loop_end = None
        elif self.book is None or not 0 <= start < end <= self.book.duration_ms:
            raise ValueError(_("The end of the repeated section must follow its start."))
        else:
            self.loop_start, self.loop_end = start, end

    def poll(self, advance=True):
        try:
            self.library.check_position_errors()
        except Exception as exc:
            self._fail(_("The listening position could not be saved: {reason}").format(reason=exc))
            return
        if self.book is None:
            return
        if self.state is State.LOADING:
            if self.clock() - self._loaded_at > 20:
                self._fail(_("Audio loading timed out. Check the recording and the audio device."))
            return
        if not self._ready:
            return
        file_position = self.backend.position()
        chapter = self.book.chapters[self.chapter_index]
        if file_position is not None and file_position >= 0:
            # A delayed timer can cross several short embedded chapters.
            while (
                file_position >= chapter.end_ms
                and self._contiguous(self.chapter_index)
                and (
                    self.sleep_boundary is None
                    or self.book.offsets[self.chapter_index + 1] < self.sleep_boundary
                )
                and (
                    self.loop_end is None
                    or self.book.offsets[self.chapter_index + 1] < self.loop_end
                )
            ):
                self.chapter_index += 1
                chapter = self.book.chapters[self.chapter_index]
            self.position_ms = min(
                self.book.offsets[self.chapter_index + 1],
                self.book.offsets[self.chapter_index] + max(0, file_position - chapter.start_ms),
            )
        if advance and self.state is State.PLAYING:
            if self._sleep_due(self.position_ms):
                self.pause()
                return
            if file_position is not None and file_position != self._progress_position:
                self._progress_position, self._progress_at = file_position, self.clock()
            elif self.clock() - self._progress_at > 8:
                self._fail(_("Playback stopped advancing. Check the audio device and try again."))
                return
            if self.loop_end is not None and self.position_ms >= self.loop_end:
                self._seek(self.loop_start, play=True)
            elif self.position_ms >= self.book.offsets[self.chapter_index + 1]:
                next_index = self.chapter_index + 1
                if self._contiguous(self.chapter_index):
                    # Continuous embedded chapters do not reopen the decoder.
                    self.chapter_index = next_index
                else:
                    self._seek(self.position_ms, play=True)
            if self.clock() - self._saved_at >= 5:
                try:
                    self._save()
                except Exception as exc:
                    self._fail(
                        _("The listening position could not be saved: {reason}").format(reason=exc)
                    )

    def _contiguous(self, index):
        chapters = self.book.chapters
        return (
            index + 1 < len(chapters)
            and chapters[index + 1].path == chapters[index].path
            and chapters[index + 1].start_ms == chapters[index].end_ms
        )
