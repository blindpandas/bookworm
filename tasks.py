# coding: utf-8

"""
This file contains Bookworm's build system.
It uses the `invoke` package to define and run commands.
"""

import sys
import os
import platform
import shutil
import json 
from io import BytesIO, StringIO
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from lzma import compress
from invoke import task, call
from invoke.exceptions import UnexpectedExit
from PIL import Image
from wx.tools.img2py import img2py
from mistune import markdown


PROJECT_ROOT = Path.cwd()
PACKAGE_FOLDER = PROJECT_ROOT / "bookworm"
GUIDE_HTML_TEMPLATE = """<!doctype html>
  <html lang="{lang}">
  <head>
  <title>{title}</title>
  </head>
  <body>
  {content}
  </body>
  </html>
"""

@contextmanager
def mute_stdout():
    _stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield
    finally:
        sys.stdout = _stdout
        
        
def _add_envars(context):
    from bookworm import app

    arch = app.arch
    build_folder = PROJECT_ROOT / "scripts" / "builder" / "dist" / arch / "Bookworm"
    context["build_folder"] = build_folder
    os.environ.update(
        {
            "IAPP_ARCH": arch,
            "IAPP_NAME": app.name,
            "IAPP_DISPLAY_NAME": app.display_name,
            "IAPP_VERSION": app.version,
            "IAPP_VERSION_EX": app.version_ex,
            "IAPP_AUTHOR": app.author,
            "IAPP_WEBSITE": app.website,
            "IAPP_COPYRIGHT": app.copyright,
            "IAPP_FROZEN_DIRECTORY": str(build_folder),
        }
    )
    context["_envars_added"] = True


def make_env(func):
    """Set the necessary environment variables."""

    @wraps(func)
    def wrapper(c, *args, **kwargs):
        if not c.get("_envars_added"):
            print("Adding environment variables...")
            _add_envars(c)
        return func(c, *args, **kwargs)

    return wrapper


@task(name="icons")
def make_icons(c):
    """Rescale images and embed them in a python module."""
    print("Rescaling images and embedding them in bookworm.resources.images.py")
    TARGET_SIZE = (24, 24)
    IMAGE_SOURCE_FOLDER = PROJECT_ROOT / "fullsize_images"
    PY_MODULE = PACKAGE_FOLDER / "resources" / "images.py"
    if PY_MODULE.exists():
        PY_MODULE.unlink()
    with TemporaryDirectory() as temp:
        for index, imgfile in enumerate(Path(IMAGE_SOURCE_FOLDER).iterdir()):
            if imgfile.is_dir() or imgfile.suffix != ".png":
                continue
            fname = Path(temp) / imgfile.name
            Image.open(imgfile).resize(TARGET_SIZE).save(fname)
            append = bool(index)
            with mute_stdout():
                img2py(
                    python_file=str(PY_MODULE),
                    image_file=str(fname),
                    imgName=fname.name[:-4],
                    append=append,
                    compressed=True,
                )
        print("*" * 10 + " Done Embedding Images" + "*" * 10)
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "assets" / "bookworm.ico"
    if not icon_file.exists():
        print("Application icon is not there, creating it.")
        Image.open(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").resize((48, 48)).save(
            icon_file
        )
        print("Copied app icon to the assets folder.")
    bitmap_file = PROJECT_ROOT / "scripts" / "builder" / "assets" / "bookworm.bmp"
    if not bitmap_file.exists():
        print("Installer logo bitmap is not there, creating it.")
        Image.open(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").save(bitmap_file)
        print("Copied installer bitmap  to the assets folder.")
    website_header = PROJECT_ROOT / "docs" / "img" / "bookworm.png"
    if not website_header.exists():
        print("Website header logo is not there, creating it.")
        Image.open(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").resize(
            (256, 256)
        ).save(website_header)
        print("Copied website header image  to the docs folder.")


@task
def format_code(c):
    print("Formatting code to conform to our coding guidelines")
    c.run("black .")


@task(name="docs")
@make_env
def build_docs(c):
    """Build the end-user documentation."""
    print("Building documentations")
    docs_src = PROJECT_ROOT / "docs" / "userguides"
    for folder in [fd for fd in docs_src.iterdir() if fd.is_dir()]:
        lang = folder.name
        md = folder / "bookworm.md"
        html = c["build_folder"] / "resources" / "docs" / lang / "bookworm.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        content_md = md.read_text(encoding="utf8")
        content = markdown(content_md, escape=False)
        page_title = content_md.splitlines()[0].lstrip("#")
        html.write_text(
            GUIDE_HTML_TEMPLATE.format(
                lang=lang, title=page_title.strip(), content=content
            )
        )
        print("Done building the documentations.")


@task
@make_env
def copy_assets(c):
    """Copy some static assets to the new build folder."""
    print("Copying files...")
    license_file = c["build_folder"] / "resources" / "docs" / "license.txt"
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "assets" / "bookworm.ico"
    c.run(f"copy {PROJECT_ROOT / 'LICENSE'} {license_file}", hide="stdout")
    c.run(f"copy {icon_file} {c['build_folder']}", hide="stdout")
    print("Done copying files.")


@task
def copy_wx_catalogs(c):
    import wx

    src = Path(wx.__path__[0]) / "locale"
    dst = PACKAGE_FOLDER / "resources" / "locale"
    wx_langs = {fldr.name for fldr in src.iterdir() if fldr.is_dir()}
    app_langs = {fldr.name for fldr in dst.iterdir() if fldr.is_dir()}
    to_copy = wx_langs.intersection(app_langs)
    for lang in to_copy:
        c.run(
            f'copy "{src / lang / "LC_MESSAGES" / "wxstd.mo"}" "{dst / lang / "LC_MESSAGES"}"'
        )


@task
@make_env
def extract_msgs(c):
    print("Generating translation catalog template..")
    name = os.environ["IAPP_NAME"]
    author = os.environ["IAPP_AUTHOR"]
    args = " ".join(
        (
            f'-o "{str(PROJECT_ROOT / "scripts" / name)}.pot"',
            '-c "Translators:"',
            '--msgid-bugs-address "ibnomer2011@hotmail.com"',
            f'--copyright-holder="{author}"',
        )
    )
    c.run(f"pybabel extract {args} bookworm")
    print(
        "The translation catalog has been generated. You can find it in the scripts folder "
    )


@task
def compile_msgs(c):
    print("Compiling .po message catalogs to binary format.")
    domain = "bookworm"
    locale_dir = PACKAGE_FOLDER / "resources" / "locale"
    if list(locale_dir.rglob("*.po")):
        c.run(f'pybabel compile -D {domain} -d "{locale_dir}"')
        print("Done compiling message catalogs files.")
    else:
        print("No message catalogs found.")


@task(pre=(extract_msgs,))
@make_env
def update_msgs(c):
    print("Updating .po message catalogs with latest messages.")
    domain = os.environ["IAPP_NAME"]
    locale_dir = PACKAGE_FOLDER / "resources" / "locale"
    potfile = PROJECT_ROOT / "scripts" / f"{domain}.pot"
    if list(locale_dir.rglob("*.po")):
        c.run(
            f'pybabel update -i "{potfile}" -D {domain} '
            f'-d "{locale_dir}" --ignore-obsolete'
        )
        print("Done updating message catalogs files.")
    else:
        print("No message catalogs found.")


@task(pre=(extract_msgs,))
def init_lang(c, lang):
    from bookworm import app

    print(f"Creating a language catalog for language '{lang}'...")
    potfile = PROJECT_ROOT / "scripts" / f"{app.name}.pot"
    locale_dir = PACKAGE_FOLDER / "resources" / "locale"
    c.run(
        f'pybabel init -D {app.name} -i "{potfile}" '
        f'-d "{locale_dir}" --locale={lang}'
    )


@task(name="install", pre=(compile_msgs, copy_wx_catalogs))
def install_packages(c):
    print("Installing packages")
    with c.cd(str(PROJECT_ROOT / "packages")):
        pkg_names = c["packages_to_install"]
        arch = "x86" if "32bit" in platform.architecture()[0] else "x64"
        binary_packages = pkg_names[f"binary_{arch}"]
        packages = pkg_names["pure_python"] + [
            f"{arch}\\{pkg}" for pkg in binary_packages
        ]
        for package in packages:
            print(f"Installing package {package}")
            c.run(f"pip install --upgrade {package}", hide="stdout")
    with c.cd(str(PROJECT_ROOT)):
        print("Building Bookworm wheel.")
        c.run("py setup.py bdist_wheel", hide="stdout")
        wheel_path = next(Path(PROJECT_ROOT / "dist").glob("*.whl"))
        print("Installing Bookworm wheel") 
        c.run(f"pip install --upgrade {wheel_path}", hide="stdout")
    print("Finished installing packages.")


@task
@make_env
def make_installer(c):
    """Build the NSIS installer for bookworm."""
    print("Building installer for bookworm...")
    with c.cd(str(PROJECT_ROOT / "scripts")):
        c.run("makensis bookworm.nsi", hide="stdout")
        print("Setup File Build Completed.")


@task
def clean(c, assets=False, siteconfig=False):
    """Remove intermediary build files and folders."""
    with c.cd(str(PROJECT_ROOT)):
        print("Cleaning compiled bytecode cache.")
        for item in PROJECT_ROOT.iterdir():
            if not item.is_dir() or item.name.startswith("."):
                # A special folder, move on
                continue
            for pyc in PROJECT_ROOT.rglob("__pycache__"):
                shutil.rmtree(pyc, ignore_errors=True)
        print("Cleaning up temporary files and directories.")
        folders_to_clean = c["folders_to_clean"]["everytime"]
        if assets:
            folders_to_clean.extend(c["folders_to_clean"]["assets"])
        if siteconfig:
            folders_to_clean.append(".appdata")
        glob_patterns = [(entry, glob(entry)) for entry in folders_to_clean if "*" in entry]
        for entry, glbs in glob_patterns:
            folders_to_clean.remove(entry)
            folders_to_clean.extend(glbs)
        for to_remove in folders_to_clean:
            path = Path(to_remove)
            if not path.exists():
                continue
            print(f"Removing {path}")
            if path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path, ignore_errors=True)
        print("Cleaned up all intermediary build folders.")


@task
@make_env
def copy_deps(c):
    """Copies the system dlls."""
    print("Statically linking vcredis 2015 ucrt ...") 
    arch = os.environ["IAPP_ARCH"]
    dist_dir = os.environ["IAPP_FROZEN_DIRECTORY"]
    dlls = (
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\msvcp140.dll",
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.OPENMP\\vcomp140.dll",
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\vcruntime140.dll",
        f"C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\DLLs\\{arch}\\*",
    )
    for dll in dlls:
        try:
            c.run(f'copy "{dll}" "{dist_dir}"', hide="stdout")
        except UnexpectedExit:
            print(f"Faild to copy  {dll} to {dist_dir}")
            continue
    print("Static linking of vcredis 2015 ucrt is done.") 


@task
@make_env
def freeze(c):
    """Freeze the app using pyinstaller."""
    from bookworm import app

    print("Freezing the application...")
    with c.cd(str(PROJECT_ROOT / "scripts" / "builder")):
        if app.get_version_info()["pre_type"] is None:
            print("The current build is a final release. Turnning on python optimizations...")
            os.environ["PYTHONOPTIMIZE"] = "2"
        c.run(f"pyinstaller Bookworm.spec --clean -y --distpath {c['build_folder'].parent}", hide=True)
    print("App freezed. Trying to copy system dlls.")
    copy_deps(c)


@task
@make_env
def bundle_update(c):
    """Bundles the frozen app for use in updates.
    Uses zip and lzma compression.
    """    
    print("Preparing update bundle...")
    from bookworm.utils import recursively_iterdir

    env = os.environ
    frozen_dir = Path(env["IAPP_FROZEN_DIRECTORY"])
    fname = f"{env['IAPP_DISPLAY_NAME']}-{env['IAPP_VERSION']}-{env['IAPP_ARCH']}-update.bundle"
    bundle_file = PROJECT_ROOT / "scripts" / fname
    archive_file = BytesIO()
    with ZipFile(archive_file, "w") as archive:
        for file in recursively_iterdir(frozen_dir):
            archive.write(file, file.relative_to(frozen_dir))
        archive.write(PROJECT_ROOT / "scripts" / "executables" / "bootstrap.exe", "bootstrap.exe") 
    archive_file.seek(0)
    data = compress(archive_file.getbuffer())
    bundle_file.write_bytes(data)
    print("Done preparing update bundle.")


@task
def update_version_info(c):
    from bookworm import app
    from bookworm.utils import generate_sha1hash

    artifacts_folder = PROJECT_ROOT / "scripts"
    json_file =  artifacts_folder / "release-info.json"
    release_type = app.get_version_info()["pre_type"] or ""
    json_info = {release_type: {"version": app.version}}
    artifacts = dict(
        installer=artifacts_folder.glob("Bookworm*setup.exe"),
        update_bundle=artifacts_folder.glob("Bookworm*update.bundle")
    )
    for artifact_type, artifact_files in artifacts.items():
        for file in artifact_files:
            json_info[release_type][f"{file.name}.sha1hash"] = generate_sha1hash(file)
    json_file.write_text(json.dumps(json_info, indent=2))
    print("Updated version information")


@task(
    pre=(clean, make_icons, install_packages, freeze),
    post=(build_docs, copy_assets, make_installer, bundle_update)
)
@make_env
def build(c):
    """Freeze, package, and prepare the app for distribution."""


@task(name="dev", pre=(install_packages, make_icons))
def prepare_dev_environment(c):
    print("\r\nHappy hacking...")


@task(name="run")
def run_application(c, _filename=None, debug=True):
    """Runs the app."""
    try:
        from bookworm.bookworm import main
        from bookworm import app

        print(f"{app.display_name} v{app.version}")
        del main, app
    except ImportError as e:
        print("An import error was raised when trying to open the application.")
        print("Make sure that your development environment is ready.")
        print("To prepare your development environment run: invoke dev\r\n")
        print("Here is the traceback:\r\n")
        raise e
    args = []
    if _filename:
        args.append(f"--filename {_filename}")
    if debug:
        args.append("--debug")
    print(f"Debug mode is {'on' if debug else 'off'}.")
    c.run(f"py -m bookworm {' '.join(args)}")
