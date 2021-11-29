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
    "odf",
]
HIDDEN_IMPORTS = [
    "numpy",
    "cv2",
    "pkg_resources.py2_warn",
]
for package_with_submodules in HIDDEN_SUBMODULES:
    HIDDEN_IMPORTS += collect_submodules(package_with_submodules)

block_cipher = None

bookworm_a = Analysis(
    ["launcher.py"],
    pathex=[""],
    datas=DATA_FILES,
    binaries=[],
    # See: https://stackoverflow.com/questions/37815371/
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

document_indexer_a = Analysis(
    ["document_indexer.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

MERGE(
    (bookworm_a, 'launcher', 'Bookworm'),
    (document_indexer_a, 'document_indexer', 'document_indexer'),
)

bookworm_pyz = PYZ(bookworm_a.pure, bookworm_a.zipped_data, cipher=block_cipher)
bookworm_exe = EXE(
    bookworm_pyz,
    bookworm_a.scripts,
    bookworm_a.dependencies,
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

document_indexer_pyz = PYZ(
    document_indexer_a.pure, document_indexer_a.zipped_data, cipher=block_cipher
)

document_indexer_exe = EXE(
    document_indexer_pyz,
    document_indexer_a.scripts,
    document_indexer_a.dependencies,
    exclude_binaries=True,
    name="document_indexer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets\\bookworm.ico",
)

col = COLLECT(
    bookworm_exe,
    bookworm_a.binaries,
    bookworm_a.zipfiles,
    bookworm_a.datas,
    document_indexer_exe,
    document_indexer_a.binaries,
    document_indexer_a.zipfiles,
    document_indexer_a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Bookworm",
)
