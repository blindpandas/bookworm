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
    "docx",
    "pptx",
    "espeak_phonemizer",
]
BOOKWORM_RESOURCES = collect_data_files(
    "bookworm",
    excludes=[
        "*.po",
        "*.md",
    ],
)
DATA_FILES = [
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
]
HIDDEN_IMPORTS = [
    "numpy",
    "cv2",
    "pkg_resources.py2_warn",
]
for package_with_submodules in HIDDEN_SUBMODULES:
    HIDDEN_IMPORTS += collect_submodules(package_with_submodules)


block_cipher = None


a = Analysis(
    ["Bookworm.py"],
    pathex=[""],
    binaries=[],
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
