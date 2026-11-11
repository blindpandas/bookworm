"""Cancellable, verified exports. Sources and existing destinations stay intact
until the entire new file has been encoded, tagged and decoded successfully.
"""

import hashlib
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue
from threading import Event

import mutagen

from .backend import _load_mpv
from .importer import ImportCancelledError, fingerprint

FORMATS = {
    "mp3": ("mp3", "libmp3lame"),
    "m4b": ("mp4", "aac"),
    "flac": ("flac", "flac"),
    "wav": ("wav", "pcm_s16le"),
}
BITRATES = (64, 96, 128, 160, 192, 256, 320)
SAMPLE_RATES = (22050, 44100, 48000)


class ExportCancelledError(Exception):
    pass


@dataclass(frozen=True)
class ExportOptions:
    format: str = "mp3"
    bitrate: int = 128
    sample_rate: int = 44100
    channels: int = 2
    rate: float = 1.0
    boost: float = 0.0

    def __post_init__(self):
        if (
            self.format not in FORMATS
            or self.bitrate not in BITRATES
            or self.sample_rate not in SAMPLE_RATES
            or self.channels not in (1, 2)
        ):
            raise ValueError(_("Invalid audio export settings."))
        if not math.isfinite(self.rate) or not 0.5 <= self.rate <= 2:
            raise ValueError(_("Playback speed must be between 50% and 200%."))
        if not math.isfinite(self.boost) or not 0 <= self.boost <= 12:
            raise ValueError(_("Speech boost must be between 0 and 12 dB."))
        if self.format == "mp3" and self.sample_rate == 22050 and self.bitrate > 160:
            raise ValueError(_("MP3 at 22050 Hz supports a maximum bitrate of 160 kbit/s."))

    def estimated_bytes(self, duration_ms):
        # A floating-point PCM intermediate preserves R3 output without clipping
        # or lossy re-encoding. Its space is checked before starting.
        bits = (
            self.sample_rate * self.channels * 16
            if self.format in ("flac", "wav")
            else self.bitrate * 1000
        )
        raw = self.sample_rate * self.channels * 4
        return int(duration_ms / 1000 / self.rate * (raw + bits / 8) * 1.15) + 16 * 1024 * 1024


def ffmpeg_path():
    if sys.platform == "win32":
        from bookworm import app

        folder = (
            Path(sys._MEIPASS) / "audio-engine"
            if app.is_frozen
            else Path(__file__).resolve().parents[2] / "scripts" / "dlls" / "mpv" / app.arch
        )
        path = folder / "ffmpeg.exe"
    else:
        path = Path(shutil.which("ffmpeg") or "/nonexistent/bookworm-ffmpeg")
    if not path.is_file():
        raise RuntimeError(
            _("The audio export engine is missing. Please reinstall a complete Bookworm build.")
        )
    return str(path)


def _check_cancel(cancel):
    if cancel.is_set():
        raise ExportCancelledError


def source_files(book, cancel=None):
    """Validate every unique source, preserving book order."""
    sources = {}
    for index, chapter in enumerate(book.chapters):
        if cancel is not None:
            _check_cancel(cancel)
        if chapter.path in sources:
            continue
        path = book.absolute_path(index)
        try:
            actual = fingerprint(path, cancel)
        except ImportCancelledError as exc:
            raise ExportCancelledError from exc
        if path.stat().st_size != chapter.size or actual != chapter.fingerprint:
            raise ValueError(_("The recording has changed. Import it as a new book."))
        sources[chapter.path] = path
    return sources


def _signature(path):
    if not path.exists():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_ino


def _destination(path, sources, overwrite):
    path = Path(path).resolve()
    if path in sources.values() or any(
        path.exists() and path.samefile(p) for p in sources.values()
    ):
        raise ValueError(
            _("Choose a different destination. Original recordings cannot be overwritten.")
        )
    if path.exists() and (not overwrite or not path.is_file()):
        raise FileExistsError(_("The destination already exists. Choose another name."))
    if not path.parent.is_dir():
        raise ValueError(_("The destination folder does not exist."))
    return path, _signature(path)


def _commit(temporary, target, initial_signature):
    if _signature(target) != initial_signature:
        raise FileExistsError(_("The destination changed during export. Choose another name."))
    os.replace(temporary, target)


def save_copy(book, target, cancel=None, progress=None, *, overwrite=False):
    """One source: save a byte-identical file. Multiple sources: a new folder."""
    cancel = cancel or Event()
    _check_cancel(cancel)
    sources = source_files(book, cancel)
    target, signature = _destination(target, sources, overwrite if len(sources) == 1 else False)
    if (
        len(sources) == 1
        and target.suffix.casefold() != next(iter(sources.values())).suffix.casefold()
    ):
        raise ValueError(_("An unchanged copy must keep the original file extension."))
    total = sum(p.stat().st_size for p in sources.values())
    if shutil.disk_usage(target.parent).free < total + 1024 * 1024:
        raise OSError(_("There is not enough free space at the destination."))
    with tempfile.TemporaryDirectory(prefix=".bookworm-copy-", dir=target.parent) as temporary:
        temporary = Path(temporary)
        output = temporary / "copy"
        if len(sources) > 1:
            output.mkdir()
        copied = 0
        for relative, source in sources.items():
            destination = output / relative if len(sources) > 1 else output
            destination.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with source.open("rb") as incoming, destination.open("xb") as outgoing:
                while chunk := incoming.read(1024 * 1024):
                    _check_cancel(cancel)
                    outgoing.write(chunk)
                    digest.update(chunk)
                    copied += len(chunk)
                    if progress:
                        progress(_("Copying original recordings"), min(99, copied * 100 // total))
                outgoing.flush()
                os.fsync(outgoing.fileno())
            with destination.open("rb") as stream:
                actual = hashlib.sha256()
                while chunk := stream.read(1024 * 1024):
                    _check_cancel(cancel)
                    actual.update(chunk)
            if actual.digest() != digest.digest():
                raise OSError(_("The saved copy failed verification."))
        source_files(book, cancel)  # Detect replacement while reading.
        _check_cancel(cancel)
        _commit(output, target, signature)
    return target


def _edl_quote(value):
    return f"%{len(value.encode('utf-8'))}%{value}"


def _edl(book):
    # This trusted EDL is generated only from validated local paths. Length
    # quoting is byte-based, including Unicode, commas, percent signs and newlines.
    return "edl://!no_chapters;" + ";".join(
        f"{_edl_quote(str(book.absolute_path(i)))},{c.start_ms / 1000:.3f},{c.duration_ms / 1000:.3f}"
        for i, c in enumerate(book.chapters)
    )


def _metadata_escape(value):
    return "".join("\\" + c if c in "\\=;#\n" else c for c in value.replace("\r", ""))


def _metadata(book, rate):
    lines = [
        ";FFMETADATA1",
        "title=" + _metadata_escape(book.title),
        "album=" + _metadata_escape(book.title),
        "artist=" + _metadata_escape(book.author),
    ]
    for i, chapter in enumerate(book.chapters):
        lines.extend(
            (
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={round(book.offsets[i] / rate)}",
                f"END={round(book.offsets[i + 1] / rate)}",
                "title=" + _metadata_escape(chapter.title),
            )
        )
    return "\n".join(lines) + "\n"


def _render_pcm(book, path, options, cancel, progress):
    ended = Queue()
    errors = []

    def log(level, _prefix, message):
        if level in ("error", "fatal") and len(errors) < 20:
            errors.append(message.strip())

    player = _load_mpv().MPV(
        config=False,
        load_scripts=False,
        ytdl=False,
        video=False,
        terminal=False,
        idle=True,
        input_default_bindings=False,
        input_vo_keyboard=False,
        ao="pcm",
        ao_pcm_file=str(path),
        ao_pcm_waveheader=False,
        audio_samplerate=options.sample_rate,
        audio_channels="mono" if options.channels == 1 else "stereo",
        audio_format="float",
        audio_pitch_correction=True,
        af="rubberband=engine=finer:pitch-scale=1.0" if options.rate != 1 else "",
        speed=options.rate,
        volume=100,
        log_handler=log,
    )

    @player.event_callback("end-file")
    def finished(event):
        ended.put(event.data.reason)

    try:
        player.play(_edl(book))
        previous, last_progress = -1, time.monotonic()
        while True:
            _check_cancel(cancel)
            try:
                reason = ended.get(timeout=0.1)
                if reason not in (0, "eof"):
                    raise RuntimeError(
                        _("Audio encoding failed: {reason}").format(reason="; ".join(errors))
                    )
                break
            except Empty:
                position = player.time_pos
                if position is not None and position > previous:
                    previous, last_progress = position, time.monotonic()
                if progress:
                    progress(
                        _("Encoding audiobook"),
                        min(99, round(max(0, previous) * 100000 / book.duration_ms)),
                    )
                if time.monotonic() - last_progress > 120:
                    raise TimeoutError(_("Audio export stopped responding."))
    finally:
        player.terminate()  # Flush codec and container before probing/remuxing.
    if errors:
        raise RuntimeError(_("Audio encoding failed: {reason}").format(reason="; ".join(errors)))


def _run_ffmpeg(command, cancel):
    with tempfile.TemporaryFile() as error:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=error,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        try:
            while process.poll() is None:
                if cancel.wait(0.1):
                    raise ExportCancelledError
            if process.returncode:
                error.seek(0)
                reason = error.read(4096).decode("utf-8", errors="replace")
                raise RuntimeError(_("Audio processing failed: {reason}").format(reason=reason))
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)


def verify_recordings(book, cancel=None, progress=None):
    """Decode every audio stream completely, without sending sound to a device."""
    cancel = cancel or Event()
    executable = ffmpeg_path()
    sources = source_files(book, cancel)
    for index, (name, source) in enumerate(sources.items()):
        _check_cancel(cancel)
        if progress:
            progress(index + 1, len(sources), name)
        _run_ffmpeg(
            [
                executable,
                "-nostdin",
                "-v",
                "error",
                "-xerror",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-f",
                "null",
                "-",
            ],
            cancel,
        )
    source_files(book, cancel)
    _check_cancel(cancel)
    return book


def export_book(book, target, options, cancel=None, progress=None, *, overwrite=False):
    cancel = cancel or Event()
    _check_cancel(cancel)
    sources = source_files(book, cancel)
    target, signature = _destination(target, sources, overwrite)
    if target.suffix.casefold() != "." + options.format:
        raise ValueError(_("The file extension must match the selected audio format."))
    executable = ffmpeg_path()
    if shutil.disk_usage(target.parent).free < options.estimated_bytes(book.duration_ms):
        raise OSError(_("There is not enough free space at the destination."))
    with tempfile.TemporaryDirectory(prefix=".bookworm-export-", dir=target.parent) as temporary:
        temporary = Path(temporary)
        encoded = temporary / "rendered.f32"
        final = temporary / ("verified." + options.format)
        metadata = temporary / "chapters.txt"
        metadata.write_text(_metadata(book, options.rate), encoding="utf-8")
        _render_pcm(book, encoded, options, cancel, progress)
        if progress:
            progress(_("Encoding audio and saving chapters"), 0)
        command = [
            executable,
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-f",
            "f32le",
            "-ar",
            str(options.sample_rate),
            "-ac",
            str(options.channels),
            "-i",
            str(encoded),
            "-i",
            str(metadata),
            "-map",
            "0:a:0",
            "-map_metadata",
            "1",
            "-map_chapters",
            "1" if options.format in ("mp3", "m4b") else "-1",
            "-c:a",
            FORMATS[options.format][1],
        ]
        if options.rate != 1 or options.boost:
            command.extend(
                (
                    "-af",
                    f"volume={options.boost:g}dB,alimiter=limit=0.891251:level=0:attack=5:release=100:latency=1",
                )
            )
        if options.format in ("mp3", "m4b"):
            command.extend(("-b:a", f"{options.bitrate}k"))
        else:
            command.extend(("-sample_fmt", "s16"))
        if options.format == "m4b":
            command.extend(("-movflags", "+faststart"))
        if options.format == "mp3":
            command.extend(("-id3v2_version", "3"))
        if options.format == "wav":
            command.extend(("-rf64", "auto"))
        _run_ffmpeg([*command, str(final)], cancel)
        if progress:
            progress(_("Verifying the complete audio file"), 0)
        _run_ffmpeg(
            [
                executable,
                "-nostdin",
                "-v",
                "error",
                "-xerror",
                "-i",
                str(final),
                "-map",
                "0:a:0",
                "-f",
                "null",
                "-",
            ],
            cancel,
        )
        audio = mutagen.File(final)
        expected_seconds = book.duration_ms / 1000 / options.rate
        if (
            audio is None
            or audio.info.sample_rate != options.sample_rate
            or audio.info.channels != options.channels
            or abs(audio.info.length - expected_seconds) > max(0.5, expected_seconds * 0.002)
        ):
            raise ValueError(
                _("The exported audio does not match the requested duration or format.")
            )
        if options.format == "mp3" and abs(audio.info.bitrate - options.bitrate * 1000) > 1000:
            raise ValueError(_("The exported audio does not match the requested bitrate."))
        source_files(book, cancel)
        _check_cancel(cancel)
        _commit(final, target, signature)
    return target
