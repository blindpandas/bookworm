# -*- mode: python ; coding: utf-8 -*-


from pathlib import Path
import site

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


# Data files
PACKAGES_WITH_DATA = [
    "pyxpdf_data",
    "trafilatura",
    "justext",
    "tld",
    "docx",
    "pptx",
]
BOOKWORM_RESOURCES = collect_data_files(
    "bookworm",
    excludes=[
        "*.po",
        "*.md",
    ],
)
# alembic 
root = Path("../../")
# pyxpdff_data searches for a file named default.xpdf in the site-packages directory
# We need to also include this as a data file
# TODO: Find a way to move this operation under pyxpdf_data
DATA_FILES = [
    (f"{root / 'alembic/env.py'}", 'alembic'),
    (f"{root / 'alembic/versions/*'}", 'alembic/versions'),
    (f"{root / 'alembic.ini'}", '.'),
]
DATA_FILES += [
    (
        src,
        Path(dst).relative_to("bookworm"),
    )
    for src, dst in BOOKWORM_RESOURCES
]
for pkg_name in PACKAGES_WITH_DATA:
    DATA_FILES += collect_data_files(pkg_name)

# Hidden imports
HIDDEN_SUBMODULES = [
    "babel",
    "cssselect",
    "odf",
    "trafilatura",
    "justext",
    "winrt",
]
HIDDEN_IMPORTS = [
    "mpv",
    "mutagen.mp3",
    "mutagen.mp4",
    "mutagen.wave",
    "mutagen.flac",
    "mutagen.oggvorbis",
    "mutagen.oggopus",
    "alembic",
    "numpy",
    "cv2",
    "logging.config",
    "winrt.windows.foundation",
    "winrt.windows.foundation.collections",
    "winrt.windows.globalization",
    "winrt.windows.graphics.imaging",
    "winrt.windows.media",
    "winrt.windows.media.ocr",
    "winrt.windows.media.speechsynthesis",
    "winrt.windows.storage.streams",
]
for package_with_submodules in HIDDEN_SUBMODULES:
    HIDDEN_IMPORTS += collect_submodules(package_with_submodules)


block_cipher = None

# Fail the build instead of shipping controls backed by missing native engines.
import struct
audio_arch = "x64" if struct.calcsize("P") == 8 else "x86"
audio_folder = root / "scripts" / "dlls" / "mpv" / audio_arch
audio_binaries = []
for audio_binary in ("libmpv-2.dll", "ffmpeg.exe"):
    if not (audio_folder / audio_binary).is_file():
        raise RuntimeError("Run scripts/prepare_audio_engine.py for the build architecture first")
    audio_binaries.append((str(audio_folder / audio_binary), "audio-engine"))
DATA_FILES.extend((str(path), "audio-engine") for path in audio_folder.glob("*.txt"))

# Also protect direct PyInstaller invocations, not only the invoke build task.
import runpy
audio_runtime = runpy.run_path(str(root / "scripts" / "prepare_audio_engine.py"))
audio_runtime["verify_runtime"](audio_arch)


a = Analysis(
    ["Bookworm.py"],
    pathex=[""],
    binaries=audio_binaries,
    datas=DATA_FILES,
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.dependencies,
    exclude_binaries=True,
    name="Bookworm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="assets\\version_info.txt",
    icon="assets\\bookworm.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Bookworm",
)
