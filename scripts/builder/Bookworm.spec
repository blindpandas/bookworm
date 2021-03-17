# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


# Data files
PACKAGES_WITH_DATA = [
    "pyxpdf_data",
    "trafilatura",
    "justext",
    "tld",
    "lazy_import",
]
BOOKWORM_RESOURCES = collect_data_files('bookworm', excludes=['*.po',])
DATA_FILES = [
    (src, Path(dst).relative_to("bookworm"),)
    for src, dst in BOOKWORM_RESOURCES
]
for pkg_name in PACKAGES_WITH_DATA:
    DATA_FILES += collect_data_files(pkg_name)

# Hidden imports
HIDDEN_IMPORTS = ["numpy", "cv2", "pkg_resources.py2_warn",] + collect_submodules("babel")

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
    excludes=["tkinter",],
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
