# coding: utf-8

import struct
import os
import platform
import shutil
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from invoke import task
from invoke.exceptions import UnexpectedExit
from PIL import Image
from wx.tools.img2py import img2py
from mistune import markdown


PROJECT_ROOT = Path.cwd()
PACKAGE_FOLDER = PROJECT_ROOT / "bookworm"


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
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "artifacts" / "bookworm.ico"
    if not icon_file.exists():
        print("Application icon is not there, creating it.")
        Image.open(IMAGE_SOURCE_FOLDER / "ico" / "bookworm.png").resize((48, 48)).save(
            icon_file
        )
        print("Copied app icon to the artifacts folder.")
    bitmap_file = PROJECT_ROOT / "scripts" / "builder" / "artifacts" / "bookworm.bmp"
    if not bitmap_file.exists():
        print("Installer logo bitmap is not there, creating it.")
        Image.open(IMAGE_SOURCE_FOLDER / "ico" / "bookworm.png").save(bitmap_file)
        print("Copied installer bitmap  to the artifacts folder.")


@task
def format_code(c):
    print("Formatting code to conform to our coding guidelines")
    c.run("black .")


@task(name="docs")
def build_docs(c):
    """Build the end-user documentation."""
    print("Building documentations")
    md = PROJECT_ROOT / "docs" / "bookworm.md"
    html = c.build_folder / "resources" / "docs" / "bookworm.html"
    html.parent.mkdir(parents=True, exist_ok=True)
    content = md.read_text(encoding="utf8")
    text_md = markdown(content, escape=False)
    html.write_text(
        f"""
        <!doctype html>
        <html>
        <head>
        <title>Bookworm User Manual</title>
        </head>
        <body>
        {text_md}
        </body>
        </html>
    """
    )
    print("Done building the documentations.")


@task
def copy_artifacts(c):
    """Copy some static artifacts to the new build folder."""
    print("Copying files...")
    license_file = c.build_folder / "resources" / "docs" / "license.txt"
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "artifacts" / "bookworm.ico"
    c.run(f"copy {PROJECT_ROOT / 'LICENSE'} {license_file}")
    c.run(f"copy {icon_file} {c.build_folder}")
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
def make_installer(c):
    """Build the NSIS installer for bookworm."""
    from bookworm import app

    os.environ.update(
        {
            "IAPP_NAME": app.name,
            "IAPP_DISPLAY_NAME": app.display_name,
            "IAPP_VERSION": app.version,
            "IAPP_VERSION_EX": app.version_ex,
            "IAPP_AUTHOR": app.author,
            "IAPP_WEBSITE": app.website,
            "IAPP_COPYRIGHT": app.copyright,
        }
    )
    with c.cd(str(PROJECT_ROOT / "scripts")):
        c.run("makensis bookworm.nsi")
        print("Setup File Build Completed.")


@task(name="clean")
def clean_after(c, artifacts=False, siteconfig=False):
    """Remove intermediary build folders."""
    with c.cd(str(PROJECT_ROOT)):
        print("Cleaning compiled bytecode cache.")
        for pyc in PROJECT_ROOT.rglob("__pycache__"):
            shutil.rmtree(pyc, ignore_errors=True)
        print("Cleaning up temporary files and directories.")
        folders_to_clean = c["folders_to_clean"]["everytime"]
        if artifacts:
            folders_to_clean.extend(c["folders_to_clean"]["artifacts"])
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


@task(
    pre=(install_packages, make_icons),
    post=(build_docs, copy_artifacts, make_installer),
)
def build(c):
    """Freeze, package, and prepare the app for distribution."""
    arch = "x86" if struct.calcsize("P") == 4 else "x64"
    os.environ["IAPP_ARCH"] = arch
    build_folder = PROJECT_ROOT / "scripts" / "builder" / "dist" / arch
    c.config["build_folder"] = build_folder / "Bookworm"
    with c.cd(str(build_folder.parent.parent)):
        c.run(f"pyinstaller Bookworm.spec -y --distpath {build_folder}")


@task(name="dev", pre=(install_packages, make_icons))
def prepare_dev_environment(c):
    print("\r\nHappy hacking...")


@task(name="run")
def run_application(c, debug=True):
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
    os.environ.setdefault("BOOKWORM_DEBUG", str(int(debug)))
    c.run("py -m bookworm")
