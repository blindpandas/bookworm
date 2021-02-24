# coding: utf-8

"""
This file contains Bookworm's build system.
It uses the `invoke` command runner to define and run commands.
"""

import sys
import os
import platform
import shutil
import json
from io import BytesIO, StringIO
from datetime import datetime
from functools import wraps
from contextlib import redirect_stdout
from glob import glob
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_LZMA
from jinja2 import Environment, FileSystemLoader
from invoke import task, call
from invoke.exceptions import UnexpectedExit


PROJECT_ROOT = Path.cwd()
PACKAGE_FOLDER = PROJECT_ROOT / "bookworm"
RESOURCES_FOLDER = PACKAGE_FOLDER / "resources"
ICON_SIZE = (256, 256)
GUIDE_HTML_TEMPLATE = """
<!doctype html>
  <html lang="{lang}">
  <head>
  <title>{title}</title>
  </head>
  <body>
  {content}
  </body>
  </html>
""".strip()


def invert_image(image_path):
    from PIL import Image
    from fitz import Pixmap

    pix = Pixmap(image_path)
    pix.invertIRect(pix.irect)
    buffer = BytesIO(pix.getImageData())
    del pix
    return Image.open(buffer)


def make_installer_image(logo_file):
    from PIL import Image
    from PIL.ImageColor import getrgb

    color = getrgb("#77216F")
    logo = Image.open(logo_file).convert("RGB").resize((164, 164))
    newdata = []
    for item in logo.getdata():
        if item == (0, 0, 0):
            newdata.append(color)
        else:
            newdata.append(item)
    logo.putdata(newdata)
    region = logo.crop((0, 0, 164, 164))
    img = Image.new("RGB", (164, 314), color)
    img.paste(region, (0, 75))
    return img


def _add_envars(context):
    sys.path.insert(0, str(PACKAGE_FOLDER))
    import app

    del sys.path[0]

    arch = app.arch
    build_folder = PROJECT_ROOT / "scripts" / "builder" / "dist" / arch / "Bookworm"
    context["build_folder"] = build_folder
    os.environ.update(
        {
            "IAPP_ARCH": arch,
            "IAPP_NAME": app.name,
            "IAPP_DISPLAY_NAME": app.display_name,
            "IAPP_DESCRIPTION": app.description,
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
    from PIL import Image
    from PIL import ImageOps
    from wx.tools.img2py import img2py

    TARGET_SIZE = (24, 24)
    IMAGE_SOURCE_FOLDER = PROJECT_ROOT / "fullsize_images"
    PY_MODULE = PACKAGE_FOLDER / "resources" / "image_data.py"
    print(f"Rescaling images and embedding them in {PY_MODULE}")
    if PY_MODULE.exists():
        PY_MODULE.unlink()
    with TemporaryDirectory() as temp:
        for index, imgfile in enumerate(Path(IMAGE_SOURCE_FOLDER).iterdir()):
            filename, ext = os.path.splitext(imgfile.name)
            if imgfile.is_dir() or ext != ".png":
                continue
            save_target = Path(temp) / imgfile.name
            save_target_hc = Path(temp) / f"{filename}.hg{ext}"
            Image.open(imgfile).resize(TARGET_SIZE).save(save_target)
            # Create an inverted version for high contrast
            invert_image(str(imgfile)).resize(TARGET_SIZE).save(save_target_hc)
            append = bool(index)
            with redirect_stdout(StringIO()):
                img2py(
                    python_file=str(PY_MODULE),
                    image_file=str(save_target),
                    imgName=f"_{filename}",
                    append=append,
                    compressed=True,
                )
                img2py(
                    python_file=str(PY_MODULE),
                    image_file=str(save_target_hc),
                    imgName=f"_{filename}_hc",
                    append=True,
                    compressed=True,
                )
        # Fix for some import issues with Img2Py
        imgdata_py = PY_MODULE.read_text()
        imp_statement = "from wx.lib.embeddedimage import PyEmbeddedImage"
        if imp_statement not in imgdata_py:
            PY_MODULE.write_text(f"{imp_statement}\n{imgdata_py}")
        print("*" * 10 + " Done Embedding Images" + "*" * 10)
    print("Creating installer images...")
    inst_dst = PROJECT_ROOT / "scripts" / "builder" / "assets"
    inst_imgs = {
        "bookworm.ico": ICON_SIZE,
        "bookworm.bmp": (48, 48),
    }
    make_installer_image(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").save(
        inst_dst / "bookworm-logo.bmp"
    )
    for fname, imgsize in inst_imgs.items():
        imgfile = inst_dst.joinpath(fname)
        if not imgfile.exists():
            print(f"Creating image {fname}.")
            Image.open(IMAGE_SOURCE_FOLDER / "logo" / "bookworm.png").resize(
                imgsize
            ).save(imgfile)
            print(f"Copied image {fname} to the assets folder.")
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
    from mistune import markdown

    print("Building documentations")
    docs_src = PROJECT_ROOT / "docs" / "userguides"
    for folder in [fd for fd in docs_src.iterdir() if fd.is_dir()]:
        lang = folder.name
        md = folder / "bookworm.md"
        html = RESOURCES_FOLDER / "docs" / lang / "bookworm.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        content_md = md.read_text(encoding="utf8")
        content = markdown(content_md, escape=False)
        page_title = content_md.splitlines()[0].lstrip("#")
        html.write_text(
            GUIDE_HTML_TEMPLATE.format(
                lang=lang, title=page_title.strip(), content=content
            ),
            encoding="utf8",
        )
        print(f"Built docs for language '{lang}'")
    print("Done building the documentations.")


@task
@make_env
def copy_assets(c):
    """Copy some static assets to the new build folder."""
    from PIL import Image

    print("Copying files...")
    files_to_copy = {
        PROJECT_ROOT / "LICENSE": RESOURCES_FOLDER / "docs" / "license.txt",
        PROJECT_ROOT
        / "contributors.txt": RESOURCES_FOLDER
        / "docs"
        / "contributors.txt",
        PROJECT_ROOT
        / "scripts"
        / "builder"
        / "assets"
        / "bookworm.ico": PACKAGE_FOLDER,
    }
    for src, dst in files_to_copy.items():
        c.run(f"cp {src} {dst}", hide="stdout")
    ficos_src = PROJECT_ROOT / "fullsize_images" / "file_icons"
    ficos_dst = RESOURCES_FOLDER / "icons"
    ficos_dst.mkdir(parents=True, exist_ok=True)
    for img in [i for i in ficos_src.iterdir() if i.suffix == ".png"]:
        Image.open(img).resize(ICON_SIZE).save(
            ficos_dst.joinpath(img.name.split(".")[0] + ".ico")
        )
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
            f'cp "{src / lang / "LC_MESSAGES" / "wxstd.mo"}" "{dst / lang / "LC_MESSAGES"}"'
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
@make_env
def compile_msgs(c):
    print("Compiling .po message catalogs to binary format.")
    domain = os.environ["IAPP_NAME"]
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
        glob_patterns = [
            (entry, glob(entry)) for entry in folders_to_clean if "*" in entry
        ]
        for entry, glbs in glob_patterns:
            folders_to_clean.remove(entry)
            folders_to_clean.extend(glbs)
        for to_remove in folders_to_clean:
            path = Path(os.path.normpath(to_remove))
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
    if sys.platform != "win32":
        return print("Not Windows")
    print("Copying vcredis 2015 ucrt support DLLs...")
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
            c.run(f'cp "{dll}" "{dist_dir}"', hide="stdout")
        except UnexpectedExit:
            print(f"Faild to copy  {dll} to {dist_dir}")
            continue
    print("Done copying vcredis 2015 ucrt DLLs.")


@task
@make_env
def bundle_update(c):
    """
    Bundles the frozen app for use in updates.
    Uses zip and lzma compression.
    """
    print("Preparing update bundle...")
    if sys.platform != "win32":
        print("Update bundles are only supported for Windows. Skipping...")
        return
    from bookworm.utils import recursively_iterdir

    env = os.environ
    frozen_dir = Path(env["IAPP_FROZEN_DIRECTORY"])
    fname = f"{env['IAPP_DISPLAY_NAME']}-{env['IAPP_VERSION']}-{env['IAPP_ARCH']}-update.bundle"
    bundle_file = PROJECT_ROOT / "scripts" / fname
    with ZipFile(bundle_file, "w", compression=ZIP_LZMA, allowZip64=False) as archive:
        for file in recursively_iterdir(frozen_dir):
            archive.write(file, file.relative_to(frozen_dir))
        archive.write(
            PROJECT_ROOT / "scripts" / "executables" / "bootstrap.exe", "bootstrap.exe"
        )
    print("Done preparing update bundle.")


@task
def update_version_info(c):
    from bookworm import app
    from bookworm.utils import generate_sha1hash

    artifacts_folder = PROJECT_ROOT / "scripts"
    json_file = artifacts_folder / "release-info.json"
    release_type = app.get_version_info()["pre_type"] or ""
    json_info = {release_type: {"version": app.version}}
    artifacts = dict(
        installer=artifacts_folder.glob("Bookworm*setup.exe"),
        update_bundle=artifacts_folder.glob("Bookworm*update.bundle"),
    )
    for artifact_type, artifact_files in artifacts.items():
        for file in artifact_files:
            json_info[release_type][f"{file.name}.sha1hash"] = generate_sha1hash(file)
    json_file.write_text(json.dumps(json_info, indent=2))
    print("Updated version information")


@task(name="libs")
@make_env
def copy_uwp_services_lib(c):
    if sys.platform != "win32":
        return print("Not Windows.")
    build_config = "Release" if "APPVEYOR_BUILD_FOLDER" in os.environ else "Debug"
    uwp_services_path = PROJECT_ROOT / "includes" / "BookwormUWPServices"
    src = uwp_services_path / "bin" / build_config / "BookwormUWPServices.dll"
    dst = c["build_folder"]
    c.run(f"cp {src} {dst}")


@task
@make_env
def install_local_packages(c):
    print("Upgrading pip...")
    c.run("python -m pip install --upgrade pip")
    print("Installing local packages")
    arch = os.environ["IAPP_ARCH"]
    pkg_names = c["packages_to_install"]
    packages = pkg_names["pure_python"] or []
    if sys.platform in pkg_names:
        platform_packages = pkg_names[sys.platform]
        pure_python = platform_packages["pure_python"]
        binary_packages = platform_packages[arch]
        if pure_python:
            packages += [Path(sys.platform) / pkg for pkg in pure_python]
        if binary_packages:
            packages += [Path(sys.platform) / arch / pkg for pkg in binary_packages]
    with c.cd(str(PROJECT_ROOT / "packages")):
        for package in packages:
            print(f"Installing package {package}")
            c.run(f"pip install --upgrade {package}", hide="stdout")


@task(pre=(install_local_packages,))
def pip_install(c):
    with c.cd(PROJECT_ROOT):
        print("Installing application dependencies using pip...")
        c.run("pip install -r requirements-dev.txt")


@task(
    name="install",
    pre=(
        pip_install,
        clean,
        make_icons,
        build_docs,
        copy_assets,
        compile_msgs,
        copy_wx_catalogs,
    ),
)
def install_bookworm(c):
    with c.cd(str(PROJECT_ROOT)):
        c.run("pip uninstall bookworm -y -q")
        if "BK_DEVELOPMENT" in c:
            c.run("pip install -e .")
        else:
            print("Building Bookworm wheel.")
            c.run("py setup.py bdist_wheel", hide="stdout")
            wheel_path = next(Path(PROJECT_ROOT / "dist").glob("*.whl"))
            print("Installing Bookworm wheel")
            c.run(f"pip install {wheel_path}", hide="stdout")
    print("Finished installing packages.")


@task
@make_env
def make_version_info_file(c):
    from bookworm import app

    print("Generating version info file...")
    env = Environment(loader=FileSystemLoader(PROJECT_ROOT / "scripts" / "builder"))
    vinfo_tpl = env.get_template("version_info.txt.tpl")
    output = vinfo_tpl.render(
        app_version_tuple=app.version_ex.replace(".", ", ").strip(),
        app_author=app.author,
        app_description=app.description,
        app_version=app.version,
        app_copyright=app.copyright,
        app_name=app.display_name,
    )
    outfile = PROJECT_ROOT / "scripts" / "builder" / "assets" / "version_info.txt"
    outfile.write_text(output)
    print(f"Version info file was generated at {outfile}")


@task(
    pre=(install_bookworm, make_version_info_file,),
    post=(
        copy_deps,
        copy_uwp_services_lib,
    ),
)
@make_env
def freeze(c):
    """Freeze the app using pyinstaller."""
    from bookworm import app

    print("Freezing the application...")
    with c.cd(str(PROJECT_ROOT / "scripts" / "builder")):
        if app.get_version_info()["pre_type"] is None:
            print(
                "The current build is a final release. Turnning on python optimizations..."
            )
            os.environ["PYTHONOPTIMIZE"] = "2"
        c.run(
            f"pyinstaller Bookworm.spec --clean -y --distpath {c['build_folder'].parent}",
            hide=True,
        )
    print("App freezed.")


@task(
    pre=(freeze,),
    post=(make_installer, bundle_update),
)
@make_env
def build(c):
    """Freeze, package, and prepare the app for distribution."""


@task(name="create-portable")
@make_env
def create_portable_copy(c):
    from bookworm.utils import recursively_iterdir

    print("Creating portable archive...")
    env = os.environ
    frozen_dir = Path(env["IAPP_FROZEN_DIRECTORY"])
    fname = f"{env['IAPP_DISPLAY_NAME']}-{env['IAPP_VERSION']}-portable.zip"
    port_arch = PROJECT_ROOT / "scripts" / fname
    with ZipFile(port_arch, "w", compression=ZIP_LZMA, allowZip64=False) as archive:
        for file in recursively_iterdir(frozen_dir):
            archive.write(file, file.relative_to(frozen_dir))
    print(f"Portable archive created at {port_arch}.")


@task(name="dev", pre=(install_bookworm,))
def prepare_dev_environment(c):
    c["BK_DEVELOPMENT"] = True
    print("\r\n🎆 Your environment is now ready for Bookworm...")
    print("😊 Happy hacking...")


@task(name="run")
def run_application(c, debug=True):
    """Runs the app."""
    try:
        # Ensure we import from source not from an installed package
        import bookworm

        if Path(bookworm.__path__[0]).parent != Path.cwd():
            print(
                "WARNGING: bookworm is being imported from a different location.\n"
                "This may happen because bookworm is not installed in dev mode.\n"
                "Changes you make in the bookworm pacakge will not show up.\n"
                "To fix this, run:\n\tpip uninstall bookworm\n\tpip install -e .\n"
            )
        from bookworm import bootstrap
        from bookworm import app

        print(f"{app.display_name} v{app.version}")
        if debug:
            os.environ["BOOKWORM_DEBUG"] = "1"
        bootstrap.run()
    except ImportError as e:
        print("An import error was raised when starting the application.")
        print("Make sure that your development environment is ready.")
        print("To prepare your development environment run: invoke dev\r\n")
        print("Here is the traceback:\r\n")
        raise
    except:
        print("An error has occured while starting Bookworm.")
        raise
