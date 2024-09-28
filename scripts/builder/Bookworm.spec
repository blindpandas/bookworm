# -*- mode: python ; coding: utf-8 -*-


from pathlib import Path
import site

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import pyxpdf_data
pyxpdf_data.get_xpdfrc_path()


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
    (f"{default_xpdf}", "lib/site-packages"),
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
]
HIDDEN_IMPORTS = [
    "alembic",
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
