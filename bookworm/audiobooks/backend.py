"""Audio-only libmpv playback with Rubber Band R3 pitch-preserving time stretching.

Native callbacks never touch wx widgets: the GUI supplies wx.CallAfter as dispatch.
Each load owns a player instance so late native events cannot target another file.
"""

import os
import sys
import time
from pathlib import Path


def audio_filters(rate, boost):
    """The same pitch/peak policy is used for playback and processed exports."""
    filters = []
    if rate != 1:
        filters.append("rubberband=engine=finer:pitch-scale=1.0")
    if boost or rate != 1:
        filters.append(
            f"lavfi=[volume={boost:g}dB,alimiter=limit=0.891251:level=0:attack=5:release=100:latency=1]"
        )
    return ",".join(filters)


def _load_mpv():
    if sys.platform == "win32":
        from bookworm import app

        if app.is_frozen:
            folder = Path(sys._MEIPASS) / "audio-engine"
        else:
            folder = Path(__file__).resolve().parents[2] / "scripts" / "dlls" / "mpv" / app.arch
        if not (folder / "libmpv-2.dll").is_file():
            raise RuntimeError(
                _("The audiobook audio engine is missing. Please use a build that includes it.")
            )
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(folder) + os.pathsep + old_path
        try:
            import mpv
        finally:
            os.environ["PATH"] = old_path
    else:
        import mpv
    return mpv


def probe_mp4_chapters(path):
    """Read QuickTime chapter tracks not covered by Mutagen's Nero chpl parser."""
    player = _load_mpv().MPV(
        config=False,
        load_scripts=False,
        ytdl=False,
        video=False,
        ao="null",
        pause=True,
        terminal=False,
    )
    try:
        with player.prepare_and_wait_for_event("file-loaded", timeout=10):
            player.play(str(Path(path).resolve()))
        return [
            (round(float(c["time"]) * 1000), c.get("title", "")) for c in player.chapter_list or []
        ]
    finally:
        player.terminate()


class MpvAudioBackend:
    def __init__(self, dispatch, player_factory=None, **options):
        self.dispatch = dispatch
        self.factory = player_factory
        self.options = options
        self.control = None
        self._pending_seek = None
        self._seek_restarted = False
        self._resume_after_seek = False
        self.rate = 1.0
        self.boost = 0.0

    def close(self):
        control, self.control = self.control, None
        self._pending_seek = None
        self._seek_restarted = False
        self._resume_after_seek = False
        if control is not None:
            control.terminate()

    def load(self, path, on_loaded, on_finished, on_error, *, rate=1.0, volume=1.0, boost=0.0):
        self.close()
        self.rate, self.boost = rate, boost
        factory = self.factory or _load_mpv().MPV
        control = factory(
            config=False,
            load_scripts=False,
            ytdl=False,
            video=False,
            input_default_bindings=False,
            input_vo_keyboard=False,
            osc=False,
            audio_display="no",
            terminal=False,
            pause=True,
            idle=True,
            audio_pitch_correction=True,
            speed=rate,
            af=audio_filters(rate, boost),
            volume=volume * 100,
            volume_max=100,
            **self.options,
        )
        self.control = control

        @control.event_callback("file-loaded", "end-file", "playback-restart")
        def event_handler(event):
            if self.control is not control:
                return
            event_id = event.event_id.value
            if event_id == 8:  # MPV_EVENT_FILE_LOADED
                self.dispatch(on_loaded)
            elif event_id == 21:  # MPV_EVENT_PLAYBACK_RESTART
                self.dispatch(self._seek_completed, control, on_error)
            elif event_id == 7:  # MPV_EVENT_END_FILE
                reason = event.data.reason
                if reason in (0, "eof"):
                    self.dispatch(on_finished)
                elif reason in (4, "error"):
                    error = event.data.error
                    message = {
                        -13: _(
                            "The audio file could not be opened. Check whether it still exists and can be read."
                        ),
                        -14: _(
                            "The audio output device could not be opened. Check the selected Windows playback device."
                        ),
                        -18: _("The recording uses an unsupported audio codec or feature."),
                        -16: _("The file does not contain a playable audio track."),
                        -17: _("The audio file format could not be recognized."),
                    }.get(
                        error,
                        _("The recording could not be decoded or the audio device is unavailable."),
                    )
                    self.dispatch(
                        on_error,
                        message,
                    )

        control.play(str(Path(path).resolve()))

    def play(self):
        if self.control is None:
            return False
        if self._pending_seek is not None:
            self._resume_after_seek = True
        else:
            self.control.pause = False
        return True

    def pause(self):
        if self.control is None:
            return False
        self.control.pause = True
        self._resume_after_seek = False
        return True

    def position(self):
        if self.control is None:
            return None
        value = self.control.time_pos
        if self._pending_seek is not None:
            if not self._verify_seek():
                return None
            value = self.control.time_pos
        return round(value * 1000) if value is not None else None

    def seek(self, position_ms):
        if self.control is None:
            return False
        if self._pending_seek is None:
            self._resume_after_seek = not self.control.pause
        self.control.pause = True
        self._pending_seek = position_ms, time.monotonic()
        self._seek_restarted = False
        self.control.command("seek", position_ms / 1000, "absolute+exact")
        return True

    def _seek_completed(self, control, on_error):
        if self.control is not control or self._pending_seek is None:
            return
        self._seek_restarted = True
        try:
            self._verify_seek()
        except (RuntimeError, ValueError) as exc:
            on_error(str(exc))

    def _verify_seek(self):
        target, started = self._pending_seek
        value = self.control.time_pos
        if self._seek_restarted and value is not None and abs(value * 1000 - target) <= 50:
            self._pending_seek = None
            self.control.pause = not self._resume_after_seek
            return True
        if time.monotonic() - started > 3:
            raise RuntimeError(
                _(
                    "The requested listening position could not be verified. Playback has been stopped."
                )
            )
        return False

    def _configure(self, rate, boost):
        if self.control is None:
            return False
        if rate == self.rate and boost == self.boost:
            return True
        old_filters = audio_filters(self.rate, self.boost)
        try:
            self.control.af = audio_filters(rate, boost)
            self.control.speed = rate
            if abs(self.control.speed - rate) >= 0.001:
                raise ValueError("Playback rate was not applied")
        except (TypeError, ValueError, RuntimeError, SystemError):
            self.control.af = old_filters
            self.control.speed = self.rate
            return False
        self.rate, self.boost = rate, boost
        return True

    def set_rate(self, rate):
        return self._configure(rate, self.boost)

    def set_boost(self, boost):
        return self._configure(self.rate, boost)

    def set_volume(self, volume):
        if self.control is None:
            return False
        self.control.volume = volume * 100
        return True
