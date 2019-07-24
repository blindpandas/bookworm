# coding: utf-8

"""
This file contains Bookworm's build system. It uses the `invoke` package to define and run commands.
"""

import struct
import os
import platform
import shutil
from functools import wraps
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from invoke import task, call
from invoke.exceptions import UnexpectedExit
from PIL import Image
from wx.tools.img2py import img2py
from mistune import markdown


PROJECT_ROOT = Path.cwd()
PACKAGE_FOLDER = PROJECT_ROOT / "bookworm"


def _add_envars(context):
    from bookworm import app

    arch = "x86" if struct.calcsize("P") == 4 else "x64"
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
            "IAPP_FROZEN_DIRECTORY": str(build_folder)
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
        Image.open(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").resize((256, 256)).save(website_header)
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
    md = PROJECT_ROOT / "docs" / "bookworm_user_guide.md"
    html = c["build_folder"] / "resources" / "docs" / "bookworm.html"
    html.parent.mkdir(parents=True, exist_ok=True)
    content = md.read_text(encoding="utf8")
    content = f"# Bookworm v{os.environ['IAPP_VERSION']} User Guide\r\r{content}"
    text_md = markdown(content, escape=False)
    html.write_text(
        f"""
        <!doctype html>
        <html>
        <head>
        <title>Bookworm v{os.environ['IAPP_VERSION']} User Guide</title>
        </head>
        <body>
        {text_md}
        </body>
        </html>
    """
    )
    print("Done building the documentations.")


@task
@make_env
def copy_assets(c):
    """Copy some static assets to the new build folder."""
    print("Copying files...")
    license_file = c["build_folder"] / "resources" / "docs" / "license.txt"
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "assets" / "bookworm.ico"
    c.run(f"copy {PROJECT_ROOT / 'LICENSE'} {license_file}")
    c.run(f"copy {icon_file} {c['build_folder']}")
    print("Done copying files.")


@task(name="install")
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
            c.run(f"pip install --upgrade {package}")
    with c.cd(str(PROJECT_ROOT)):
        c.run("py setup.py bdist_wheel")
        wheel_path = next(Path(PROJECT_ROOT / "dist").glob("*.whl"))
        c.run(f"pip install --upgrade {wheel_path}")
    print("Finished installing packages.")


@task
@make_env
def make_installer(c):
    """Build the NSIS installer for bookworm."""
    with c.cd(str(PROJECT_ROOT / "scripts")):
        c.run("makensis bookworm.nsi")
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
        glob_patterns = ((i, entry) for (i, entry) in enumerate(folders_to_clean) if "*" in entry)
        for idx, glb in glob_patterns:
            folders_to_clean.pop(idx)
            folders_to_clean.extend(glob(glb))
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
    arch = os.environ["IAPP_ARCH"]
    dist_dir = os.environ["IAPP_FROZEN_DIRECTORY"]
    dlls = (
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\msvcp140.dll",
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.OPENMP\\vcomp140.dll",
        f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\vcruntime140.dll",
        f"C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\DLLs\\{arch}\\*"
    )
    for dll in dlls:
        print(f"Copying {dll} to {dist_dir}")
        try:
            c.run(f'copy "{dll}" "{dist_dir}"')
        except UnexpectedExit:
            continue


@task
@make_env
def freeze(c):
    """Freeze the app using pyinstaller."""
    print("Freezing the application...")
    with c.cd(str(PROJECT_ROOT / "scripts" / "builder")):
        if all(ident not in os.environ["IAPP_VERSION"] for ident in ("a", "b", "dev")):
            print("Turnning on python optimizations...")
            os.environ["PYTHONOPTIMIZE"] = "2"
        c.run(f"pyinstaller Bookworm.spec -y --distpath {c['build_folder'].parent} ")
    print("Freeze finished. Trying to copy system dlls.")
    copy_deps(c)


@task(
    pre=(clean, make_icons, install_packages, freeze),
    post=(build_docs, copy_assets, make_installer),
)
@make_env
def build(c):
    """Freeze, package, and prepare the app for distribution."""
    print("Starting the build process...")


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
