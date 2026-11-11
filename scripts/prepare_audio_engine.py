"""Prepare the pinned libmpv runtime for a Windows source checkout/build.

The archive hash is mandatory. Nothing is downloaded at application runtime.
7-Zip must be installed on the build machine (present on GitHub Windows runners).
"""

import argparse
import hashlib
import shutil
import struct
import subprocess
import tempfile
import urllib.request
from pathlib import Path

RELEASE = "20261110"
REVISION = "a61f6c3abd"
ARCHIVES = {
    "x64": ("x86_64", "f07b97a72f2394a7798d6e1d36d952bbfd63577e25cef051f716751ea5dc9688", 0x8664),
    "x86": ("i686", "1c339fa75929f4a78f9fd92270ce7142f7cd723bad8aa197375c19b6504d684a", 0x14C),
}
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
    executable = shutil.which("7z") or shutil.which("7zz")
    if not executable:
        installed = Path("C:/Program Files/7-Zip/7z.exe")
        if installed.is_file():
            executable = str(installed)
    if not executable:
        raise RuntimeError("Install 7-Zip on the build machine first")
    name = f"mpv-dev-{cpu}-{RELEASE}-git-{REVISION}.7z"
    binary = "libmpv-2.dll"
    if export_engine:
        name = f"ffmpeg-{cpu}-git-{FFMPEG_REVISION}.7z"
        digest = FFMPEG_HASHES[arch]
        binary = "ffmpeg.exe"
    url = f"https://github.com/shinchiro/mpv-winbuild-cmake/releases/download/{RELEASE}/{name}"
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
            f"mpv revision: {REVISION}\nBuild recipe: https://github.com/shinchiro/mpv-winbuild-cmake\n"
            "mpv sources and license: https://github.com/mpv-player/mpv\n"
            "Rubber Band sources and license: https://breakfastquay.com/rubberband/\n"
            "FFmpeg sources and license: https://ffmpeg.org/legal.html\n"
            "Release engineering must retain corresponding source and third-party licenses.\n",
            encoding="utf-8",
        )
    return destination


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
