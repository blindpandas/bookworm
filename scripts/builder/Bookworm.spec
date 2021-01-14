# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


# Data files
BOOKWORM_RESOURCES = collect_data_files('bookworm', excludes=['*.po',])
DATA_FILES = [
    (src, Path(dst).relative_to("bookworm"),)
    for src, dst in BOOKWORM_RESOURCES
]
DATA_FILES += collect_data_files("justext")
DATA_FILES += collect_data_files("trafilatura")

# Hidden imports
HIDDEN_IMPORTS = ["pkg_resources.py2_warn"] + collect_submodules("babel")

block_cipher = None

a = Analysis(
    ["launcher.py"],
    pathex=[""],
    datas=DATA_FILES,
    binaries=[],
    # See: https://stackoverflow.com/questions/37815371/
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "PIL", "tkinter",],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Bookworm",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
