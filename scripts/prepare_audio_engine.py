"""Prepare the pinned libmpv runtime for a Windows source checkout/build.

The archive hash is mandatory. Nothing is downloaded at application runtime.
7-Zip must be installed on the build machine (present on GitHub Windows runners).
"""

import argparse
import hashlib
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

RELEASE = "20261110"
REVISION = "a61f6c3abd"
ARCHIVES = {
    "x64": ("x86_64", "f07b97a72f2394a7798d6e1d36d952bbfd63577e25cef051f716751ea5dc9688", 0x8664),
    "x86": ("i686", "9c25ba4a9381fee1bae0788e75d8a98551745e8307b1e6c2b99c0c39771b6d7b", 0x14C),
}
# The November i686 build aborts inside OpenSSL during mpv_create, before
# options can be set. The retained April build predates mpv's global libcurl
# initialization (c6833a9307, merged May 16), retaining R3 and local audio support.
MPV_BUILDS = {"x64": (RELEASE, REVISION), "x86": ("20260419", "06f4ce7")}
FFMPEG_REVISION = "b2b543c07"
FFMPEG_HASHES = {
    "x64": "ffd44a8a6f3549761ba0decad2dfc5b5fbd6fc4e9253d4c3fe83959828124085",
    "x86": "3e962c361f4aee319d76c73814f32a443666060d4c922b8b7b17d40f182c5b59",
}


def pe_machine(path):
    with Path(path).open("rb") as stream:
        if stream.read(2) != b"MZ":
            raise ValueError("The audio engine is not a Windows executable")
        stream.seek(60)
        offset = struct.unpack("<I", stream.read(4))[0]
        stream.seek(offset)
        if stream.read(4) != b"PE\0\0":
            raise ValueError("Invalid PE header")
        return struct.unpack("<H", stream.read(2))[0]


def prepare(arch, archive=None, *, export_engine=False):
    cpu, digest, machine = ARCHIVES[arch]
    release, revision = MPV_BUILDS[arch]
    executable = shutil.which("7z") or shutil.which("7zz")
    if not executable:
        installed = Path("C:/Program Files/7-Zip/7z.exe")
        if installed.is_file():
            executable = str(installed)
    if not executable:
        raise RuntimeError("Install 7-Zip on the build machine first")
    name = f"mpv-dev-{cpu}-{release}-git-{revision}.7z"
    binary = "libmpv-2.dll"
    if export_engine:
        name = f"ffmpeg-{cpu}-git-{FFMPEG_REVISION}.7z"
        digest = FFMPEG_HASHES[arch]
        binary = "ffmpeg.exe"
    url = f"https://github.com/shinchiro/mpv-winbuild-cmake/releases/download/{RELEASE}/{name}"
    if arch == "x86" and not export_engine:
        url = f"https://downloads.sourceforge.net/project/mpv-player-windows/libmpv/{name}"
    destination = Path(__file__).resolve().parent / "dlls" / "mpv" / arch
    with tempfile.TemporaryDirectory(prefix="bookworm-audio-") as temporary:
        temporary = Path(temporary)
        package = Path(archive) if archive else temporary / name
        if archive is None:
            with urllib.request.urlopen(url, timeout=60) as source, package.open("wb") as target:
                shutil.copyfileobj(source, target)
        with package.open("rb") as stream:
            actual_digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual_digest != digest:
            raise ValueError("Audio engine archive SHA-256 mismatch")
        subprocess.run(
            [
                executable,
                "x",
                "-y",
                f"-o{temporary / 'extracted'}",
                str(package.resolve()),
                binary,
            ],
            check=True,
            capture_output=True,
        )
        dll = temporary / "extracted" / binary
        if pe_machine(dll) != machine:
            raise ValueError("Audio engine architecture mismatch")
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(dll, destination / binary)
        (destination / ("EXPORT-SOURCE.txt" if export_engine else "BUILD-SOURCE.txt")).write_text(
            f"{binary} runtime\nArchive: {url}\nSHA-256: {digest}\n"
            f"Revision: {FFMPEG_REVISION if export_engine else revision}\n"
            "Build recipe: https://github.com/shinchiro/mpv-winbuild-cmake\n"
            "mpv sources and license: https://github.com/mpv-player/mpv\n"
            "Rubber Band sources and license: https://breakfastquay.com/rubberband/\n"
            "FFmpeg sources and license: https://ffmpeg.org/legal.html\n"
            "Release engineering must retain corresponding source and third-party licenses.\n",
            encoding="utf-8",
        )
    return destination


def verify_runtime(arch):
    """Reject a native abort before freezing; keep the build process alive."""
    if sys.platform != "win32":
        raise RuntimeError("Verify Windows audio engines on Windows")
    if arch != ("x64" if struct.calcsize("P") == 8 else "x86"):
        raise RuntimeError("Audio verification requires matching Python architecture")
    code = r"""
import faulthandler, tempfile, time, wave
from pathlib import Path
faulthandler.enable()
from bookworm.audiobooks.backend import create_mpv, audio_filters
with tempfile.TemporaryDirectory(prefix="Bookworm-audio-check-") as folder:
    source = Path(folder) / "audio.wav"
    with wave.open(str(source), "wb") as stream:
        stream.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        stream.writeframes(b"\x10\x00" * 22050)
    player = create_mpv(ao="null", pause=True, speed=0.75, af=audio_filters(0.75, 12))
    try:
        with player.prepare_and_wait_for_event("file-loaded", timeout=8):
            player.play(str(source))
        player.pause = False
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            position = player.time_pos
            if position is not None and position > 0.1:
                active = {f["name"] for f in player.af or [] if f.get("enabled", True)}
                if not {"rubberband", "lavfi"}.issubset(active):
                    raise RuntimeError("The required audio processing filters are not active")
                print("Verified native decode, Rubber Band R3 and limiter", flush=True)
                break
            time.sleep(0.01)
        else:
            raise RuntimeError("Audio runtime did not produce playback progress")
    finally:
        player.terminate()
"""
    result = subprocess.run(
        [sys.executable, "-u", "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    if result.returncode or "Verified native decode, Rubber Band R3 and limiter" not in result.stdout:
        raise RuntimeError(
            f"Windows audio runtime verification failed ({arch}, exit {result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    print(result.stdout.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arch", choices=ARCHIVES, default="x64" if struct.calcsize("P") == 8 else "x86"
    )
    parser.add_argument("--archive", type=Path, help="Use a previously downloaded, pinned archive")
    parser.add_argument("--export-archive", type=Path, help="Use a cached, pinned FFmpeg archive")
    args = parser.parse_args()
    print(prepare(args.arch, args.archive))
    print(prepare(args.arch, args.export_archive, export_engine=True))
    verify_runtime(args.arch)
