# coding: utf-8

import os
import platform
from pathlib import Path
from tempfile import TemporaryDirectory
from invoke import task
from invoke.exceptions import UnexpectedExit
from PIL import Image
from wx.tools.img2py import img2py
from mistune import markdown
from bs4 import BeautifulSoup


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
            Image.open(imgfile)\
            .resize(TARGET_SIZE)\
            .save(fname)
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
        Image.open(IMAGE_SOURCE_FOLDER / "ico" / "bookworm.png")\
        .resize((48, 48))\
        .save(icon_file)
        print("Copied app icon to the artifacts folder.")


@task(name="docs")
def build_docs(c):
    """Build the end-user documentation."""
    print("Building documentations")
    md = PROJECT_ROOT / "docs" / "bookworm.md"
    html =  c.build_folder / "resources" / "docs" / "bookworm.html"
    html.parent.mkdir(parents=True, exist_ok=True)
    content = md.read_text(encoding="utf8")
    content_healed = BeautifulSoup(
        markdown(content, escape=False),
        features="html.parser"
    )
    html.write_text(str(content_healed), encoding="utf8")
    print("Done building the documentations.")


@task
def copy_artifacts(c):
    """Copy some static artifacts to the new build folder."""
    print("Copying files...")
    license_file = c.build_folder / "resources" / "docs" / "license.txt"
    icon_file = PROJECT_ROOT / "scripts" / "builder" / "artifacts" / "bookworm.ico"
    c.run(f"cp {PROJECT_ROOT / 'LICENSE'} {license_file}")
    c.run(f"cp {icon_file} {c.build_folder}")
    print("Done copying files.")


@task(name="install")
def install_packages(c):
    print("Installing packages")
    c.run("pip install -r requirements.txt")
    with c.cd(str(PROJECT_ROOT / "packages")):
        pkg_names = c["packages_to_install"]
        arch = "x86" if "32bit" in platform.architecture()[0] else "x64"
        binary_packages = pkg_names[f"binary_{arch}"]
        packages = pkg_names["pure_python"] + [f"{arch}\\{pkg}" for pkg in binary_packages]
        for package in packages:
            c.run(f"pip install --upgrade {package}")
    with c.cd(str(PROJECT_ROOT)):
        c.run("py setup.py bdist_wheel")
        wheel_path = next(Path(PROJECT_ROOT / "dist").glob("*.whl"))
        c.run(f"pip install --upgrade {wheel_path}")
    print("Finished installing packages.")


@task(
    pre=(make_icons, install_packages),
    post=(build_docs, copy_artifacts,))
def build(c):
    """Freeze, package, and prepare the app for distribution."""
    build_folder = PROJECT_ROOT / "scripts" / "builder" / "dist"
    c.config["build_folder"] = build_folder / "Bookworm"
    with c.cd(str(build_folder.parent)):
        c.run(f"pyinstaller Bookworm.spec -y --distpath {build_folder}")


@task(
    name="dev",
    pre=(make_icons, install_packages))
def prepare_dev_environment(c):
    print("\r\nHappy hacking...")

@task(name="run")
def run_application(c, debug=True):
    """Runs the app."""
    try:
        c.run('pip freeze | grep "bookworm"')
    except UnexpectedExit:
        print("Looks like your development environment is not ready yet!")
        print("To prepare your development environment, please run: invoke dev")
        return
    os.environ.setdefault("BOOKWORM_DEBUG", str(int(debug)))
    c.run("py -m bookworm")
