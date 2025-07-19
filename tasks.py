# coding: utf-8

"""
This file contains Bookworm's build system.
It uses the `invoke` command runner to define and run commands.
"""

import itertools
import json
import os
import platform
import shutil
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime
from functools import wraps
from glob import glob
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_LZMA, ZipFile

from invoke import call, task
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
    from fitz import Pixmap
    from PIL import Image

    pix = Pixmap(image_path)
    pix.invert_irect(pix.irect)
    buffer = BytesIO(pix.tobytes())
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
    # From pyinstaller 6.0.0, all content except the executable and required libraries has been moved to a content directory
    # By default the directory is named _internal
    # see: https://pyinstaller.org/en/stable/CHANGES.html#id66
    build_folder_content = build_folder / "_internal"
    context["offline_run"] = os.environ.get("BOOKWORM_BUILD_OFFLINE", "")
    context["build_folder"] = build_folder
    context["build_folder_content"] = build_folder_content
    context["pip_timeout"], context["pip_retries"] = (
        (1, 1) if context["offline_run"] else (15, 5)
    )
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
            "IAPP_FROZEN_CONTENT_DIRECTORY": str(build_folder_content),
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
    from PIL import Image, ImageOps
    from wx.tools.img2py import img2py

    TARGET_SIZE = (24, 24)
    IMAGE_SOURCE_FOLDER = PROJECT_ROOT / "fullsize_images"
    APP_ICONS_FOLDER = IMAGE_SOURCE_FOLDER / "app_icons"
    PY_MODULE = PACKAGE_FOLDER / "resources" / "app_icons_data.py"
    print(f"Rescaling images and embedding them in {PY_MODULE}")
    if PY_MODULE.exists():
        PY_MODULE.unlink()
    with TemporaryDirectory() as temp:
        for index, imgfile in enumerate(Path(APP_ICONS_FOLDER).iterdir()):
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
    if not inst_dst.exists():
        inst_dst.mkdir(parents=True, exist_ok=True)
    make_installer_image(IMAGE_SOURCE_FOLDER / "bookworm.png").save(
        inst_dst / "bookworm-logo.bmp"
    )
    for fname, imgsize in inst_imgs.items():
        imgfile = inst_dst.joinpath(fname)
        if not imgfile.exists():
            print(f"Creating image {fname}.")
            Image.open(IMAGE_SOURCE_FOLDER / "bookworm.png").resize(imgsize).save(
                imgfile
            )
            print(f"Copied image {fname} to the assets folder.")


@task
def format_code(c):
    print("Formatting code to conform to our coding guidelines")
    c.run("black .")


@task(name="guide")
@make_env
def build_user_guide(c):
    """Build the user guide."""
    from mistune import markdown

    print("Building the user guide...")
    guide_src = RESOURCES_FOLDER / "userguide"
    for folder in [fd for fd in guide_src.iterdir() if fd.is_dir()]:
        lang = folder.name
        md = folder / "bookworm.md"
        html = RESOURCES_FOLDER / "userguide" / lang / "bookworm.html"
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
        print(f"Built the user guide for language '{lang}'")
    print("Done building the user guide.")


@task
@make_env
def copy_assets(c):
    """Copy some static assets to the new build folder."""
    from PIL import Image

    print("Copying files...")
    files_to_copy = {
        PROJECT_ROOT / "LICENSE": RESOURCES_FOLDER / "license.txt",
        PROJECT_ROOT / "contributors.txt": RESOURCES_FOLDER / "contributors.txt",
        PROJECT_ROOT
        / "scripts"
        / "builder"
        / "assets"
        / "bookworm.ico": PACKAGE_FOLDER,
    }
    for src, dst in files_to_copy.items():
        shutil.copy(src, dst)
    ficos_src = PROJECT_ROOT / "fullsize_images" / "file_icons"
    ficos_dst = RESOURCES_FOLDER / "icons"
    ficos_dst.mkdir(parents=True, exist_ok=True)
    for img in [i for i in ficos_src.iterdir() if i.suffix == ".png"]:
        Image.open(img).resize(ICON_SIZE).save(
            ficos_dst.joinpath(img.name.split(".")[0] + ".ico")
        )
    bookshelf_ico_src = PROJECT_ROOT / "fullsize_images" / "bookshelf.png"
    bookshelf_ico_dst = PACKAGE_FOLDER / "bookshelf.ico"
    Image.open(bookshelf_ico_src).save(bookshelf_ico_dst)
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
        shutil.copy(f"{src}/{lang}/LC_MESSAGES/wxstd.mo", f"{dst}/{lang}/LC_MESSAGES")


def get_pot_filename():
    name, version = [os.environ[k] for k in ["IAPP_NAME", "IAPP_VERSION"]]
    return PROJECT_ROOT / "scripts" / f"{name}-{version}.pot"


@task(name="gen-pot")
@make_env
def generate_pot(c):
    print("Generating translation catalog template..")
    name = os.environ["IAPP_NAME"]
    display_name = os.environ["IAPP_DISPLAY_NAME"]
    author = os.environ["IAPP_AUTHOR"]
    version = os.environ["IAPP_VERSION"]
    output_filename = get_pot_filename()
    args = " ".join(
        (
            f'-o "{output_filename}"',
            '-c "Translators:"',
            '--msgid-bugs-address "ibnomer2011@hotmail.com"',
            f'--copyright-holder="{author}"',
            f'--project "{display_name}"',
            f'--version "{version}"',
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


@task(pre=(generate_pot,))
@make_env
def update_msgs(c):
    print("Updating .po message catalogs with latest messages.")
    domain = os.environ["IAPP_NAME"]
    locale_dir = PACKAGE_FOLDER / "resources" / "locale"
    potfile = get_pot_filename()
    if list(locale_dir.rglob("*.po")):
        c.run(
            f'pybabel update -i "{potfile}" -D {domain} '
            f'-d "{locale_dir}" --ignore-obsolete'
        )
        print("Done updating message catalogs files.")
    else:
        print("No message catalogs found.")


@task(pre=(generate_pot,))
def init_lang(c, lang):
    from bookworm import app

    print(f"Creating a language catalog for language '{lang}'...")
    potfile = get_pot_filename()
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
    dist_dir = c["build_folder_content"]
    dlls = [
        Path(
            f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\msvcp140.dll"
        ),
        Path(
            f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.OPENMP\\vcomp140.dll"
        ),
        Path(
            f"C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC\\redist\\{arch}\\Microsoft.VC140.CRT\\vcruntime140.dll"
        ),
    ]
    # We need all the DLLs in this subdirectory, so let's extend the list
    dlls.extend(
        list(
            Path(
                f"C:\\Program Files (x86)\\Windows Kits\\10\\Redist\\ucrt\DLLs\\{arch}"
            ).glob("*")
        )
    )
    for dll in dlls:
        try:
            shutil.copy(dll, dist_dir)
        except Exception as e:
            print(f"Failed to copy  {dll} to {dist_dir}")
            continue
    print("Done copying vcredis 2015 ucrt DLLs.")
    print("Copying Unrar DLLs")
    source_path = PROJECT_ROOT / "scripts" / "dlls" / "unrar_dll"
    unrar_dst = Path(c["build_folder_content"]) / "unrar_dll"
    unrar_dst.mkdir(parents=True, exist_ok=True)
    for file in source_path.iterdir():
        shutil.copy(file, unrar_dst)
    print("Done copying unrar DLLs")
    richeditopts_dll_src = (
        PROJECT_ROOT
        / "scripts"
        / "dlls"
        / "richeditopts"
        / os.environ["IAPP_ARCH"]
        / "BkwRicheditOpts.dll"
    )
    richeditopts_dll_dst = Path(c["build_folder_content"]) / "BkwRicheditOpts.dll"
    if not richeditopts_dll_src.exists():
        if shutil.which("cargo") is None:
            raise RuntimeError(
                "The `BkwRicheditOpts.dll` was not found, and you do not have rust toolchain installed. "
                "Please install rust or otherwise provide pre-built DLLs in the designated path."
            )
        else:
            _build_BkwRicheditOpts_dll(c)
    shutil.copy(richeditopts_dll_src, richeditopts_dll_dst)

    copy_espeak_and_piper_libs()


def copy_espeak_and_piper_libs():
    arch = os.environ["IAPP_ARCH"]

    espeak_dll_src = (
        PROJECT_ROOT / "scripts" / "dlls" / "espeak-ng" / arch / "espeak-ng.dll"
    )
    espeak_data_src = PROJECT_ROOT / "scripts" / "dlls" / "espeak-ng" / "espeak-ng-data"
    espeak_dst = Path(os.environ["IAPP_FROZEN_CONTENT_DIRECTORY"])

    print("Copying eSpeak-ng dll and data...")
    shutil.copy(espeak_dll_src, espeak_dst)
    shutil.copytree(espeak_data_src, espeak_dst.joinpath("espeak-ng-data"))

    onnxruntime_dll_src = (
        PROJECT_ROOT / "scripts" / "dlls" / "onnxruntime" / arch / "onnxruntime.dll"
    )
    onnxruntime_notices_src = (
        PROJECT_ROOT / "scripts" / "dlls" / "onnxruntime" / "notices"
    )
    onnxruntime_dst = Path(os.environ["IAPP_FROZEN_CONTENT_DIRECTORY"]) / "onnxruntime"
    onnxruntime_dst.mkdir(parents=True, exist_ok=True)

    print("Copying ONNXRuntime dll and notices...")
    shutil.copy(onnxruntime_dll_src, onnxruntime_dst)
    shutil.copytree(onnxruntime_notices_src, onnxruntime_dst.joinpath("notices"))


def _build_BkwRicheditOpts_dll(c):
    richeditopts_dll_src = PROJECT_ROOT / "scripts" / "dlls" / "richeditopts"
    targets = {"x86": "i686-pc-windows-msvc", "x64": "x86_64-pc-windows-msvc"}
    richeditopts_code_src = PROJECT_ROOT / "includes" / "bkw_rich_edit_opts"
    for arch, target in targets.items():
        with c.cd(str(richeditopts_code_src)):
            c.run(f"cargo build --release --target={target}")
            arch_richeditopts_src = richeditopts_dll_src / arch
            arch_richeditopts_src.mkdir(parents=True, exist_ok=True)
            shutil.copy(
                richeditopts_code_src
                / "target"
                / target
                / "release"
                / "BkwRicheditOpts.dll",
                arch_richeditopts_src / "BkwRicheditOpts.dll",
            )
            print("Done copying `BkwRicheditOpts.dll`")


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
    from bookworm import app
    from bookworm.utils import recursively_iterdir

    env = os.environ
    frozen_dir = Path(env["IAPP_FROZEN_DIRECTORY"])
    if app.get_version_info()["post"] is None:
        files_to_bundle = recursively_iterdir(frozen_dir)
    else:
        files_to_bundle = [
            frozen_dir / "Bookworm.exe",
        ]
    fname = f"{env['IAPP_DISPLAY_NAME']}-{env['IAPP_VERSION']}-{env['IAPP_ARCH']}-update.bundle"
    bundle_file = PROJECT_ROOT / "scripts" / fname
    with ZipFile(bundle_file, "w", compression=ZIP_LZMA, allowZip64=False) as archive:
        for file in files_to_bundle:
            archive.write(file, file.relative_to(frozen_dir))
        archive.write(
            PROJECT_ROOT / "scripts" / "executables" / "bootstrap" / "bootstrap.exe",
            "_internal/bootstrap.exe",
        )
    print("Done preparing update bundle.")


@task
def update_version_info(c):
    from bookworm import app
    from bookworm.utils import generate_sha1hash

    artifacts_folder = PROJECT_ROOT / "scripts"
    json_file = artifacts_folder / "release-info.json"
    json_info = {
        "version": app.version,
        "updated": datetime.utcnow().isoformat(),
    }
    artifacts = sorted(
        itertools.chain(
            artifacts_folder.glob("Bookworm*setup.exe"),
            artifacts_folder.glob("Bookworm*portable.zip"),
            artifacts_folder.glob("Bookworm*update.bundle"),
        )
    )
    for file in artifacts:
        json_info[f"{file.name}.sha1hash"] = generate_sha1hash(file)
    json_file.write_text(json.dumps(json_info, indent=2))
    print("Updated version information")


@task
@make_env
def gen_update_info_file(c):
    """
    Generate or update the `update_info.json` file with the latest version details,
    including download URLs and SHA1 hashes for x86 and x64 builds.
    """
    from bookworm import app
    from bookworm.utils import generate_sha1hash

    print("Generating update information file...")

    # Get the version info and determine the release channel
    version_info = app.get_version_info(app.version)
    channel = version_info.get("pre_type", "")  # Stable version if no pre_type

    # Define base URLs and file paths for x86 and x64 builds
    base_url = (
        f"https://github.com/blindpandas/bookworm/releases/download/{app.version}"
    )
    x86_file = f"{app.display_name}-{app.version}-x86-update.bundle"
    x64_file = f"{app.display_name}-{app.version}-x64-update.bundle"
    x86_download_url = f"{base_url}/{x86_file}"
    x64_download_url = f"{base_url}/{x64_file}"

    artifacts_folder = PROJECT_ROOT / "scripts"
    x86_bundle_path = artifacts_folder / x86_file
    x64_bundle_path = artifacts_folder / x64_file

    # Generate SHA1 hash or use default if file does not exist
    x86_sha1hash = (
        generate_sha1hash(x86_bundle_path)
        if x86_bundle_path.exists()
        else "example_x86_sha1hash"
    )
    x64_sha1hash = (
        generate_sha1hash(x64_bundle_path)
        if x64_bundle_path.exists()
        else "example_x64_sha1hash"
    )

    # Construct the update info dictionary
    update_info = {
        channel
        or "": {  # Ensure stable version uses an empty string key
            "version": app.version,
            "x86_download": x86_download_url,
            "x64_download": x64_download_url,
            "x86_sha1hash": x86_sha1hash,
            "x64_sha1hash": x64_sha1hash,
        }
    }

    #    update_info_file = artifacts_folder / "update_info.json"
    update_info_file = PROJECT_ROOT / "update_info.json"

    # Read the existing data if the file exists, otherwise start with an empty dictionary
    try:
        with update_info_file.open("r", encoding="utf-8") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Warning: No valid update_info.json file found. Creating a new one.")
        existing_data = {}

    # Update the existing data with the new update information
    existing_data.update(update_info)

    # Write the updated data back to the JSON file
    with update_info_file.open("w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, sort_keys=True)

    print(f"Update information file generated at {update_info_file}")


def _add_pip_install_args(cmd, context):
    return "{cmd} --timeout {timeout} --retries {retries}".format(
        cmd=cmd,
        timeout=context["pip_timeout"],
        retries=context["pip_retries"],
    )


@task
@make_env
def install_local_packages(c):
    print("Upgrading pip...")
    try:
        c.run(_add_pip_install_args("python -m pip install --upgrade pip", c))
    except UnexpectedExit as e:
        if not c["offline_run"]:
            raise e
    print("Installing local packages")
    arch = os.environ["IAPP_ARCH"]
    pkg_names = c["packages_to_install"]
    packages = pkg_names["pure_python"] or []
    if sys.platform in pkg_names:
        platform_packages = pkg_names[sys.platform]
        pure_python = platform_packages.get("pure_python", [])
        binary_packages = platform_packages[arch]
        if pure_python:
            packages += [Path(sys.platform) / pkg for pkg in pure_python]
        if binary_packages:
            packages += [Path(sys.platform) / arch / pkg for pkg in binary_packages]
    with c.cd(str(PROJECT_ROOT / "packages")):
        for package in packages:
            print(f"Installing package {package}")
            c.run(f"python -m pip install {package}")


@task(pre=(install_local_packages,))
def pip_install(c):
    with c.cd(PROJECT_ROOT):
        print("Installing application dependencies using pip...")
        try:
            c.run(
                _add_pip_install_args(
                    "python -m pip install -r requirements-dev.txt", c
                )
            )
        except UnexpectedExit as e:
            if not c["offline_run"]:
                raise e


@task(
    name="install",
    pre=(
        pip_install,
        clean,
        make_icons,
        build_user_guide,
        copy_assets,
        compile_msgs,
        copy_wx_catalogs,
    ),
)
def install_bookworm(c):
    with c.cd(str(PROJECT_ROOT)):
        c.run("python -m pip uninstall bookworm -y -q")
        if "BK_DEVELOPMENT" in c:
            c.run("python -m pip install -e .")
        else:
            print("Building Bookworm wheel.")
            c.run("python setup.py bdist_wheel")
            wheel_path = next(Path(PROJECT_ROOT / "dist").glob("*.whl"))
            print("Installing Bookworm wheel")
            c.run(f"python -m pip install {wheel_path}", hide="stdout")
    print("Finished installing packages.")


@task
@make_env
def make_version_info_file(c):
    from jinja2 import Environment, FileSystemLoader

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
    if not (parent := outfile.parent).exists():
        parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(output)
    print(f"Version info file was generated at {outfile}")


@task(
    pre=(
        install_bookworm,
        make_version_info_file,
    ),
    post=(copy_deps,),
)
@make_env
def freeze(c):
    """Freeze the app using pyinstaller."""

    from bookworm import app

    print("Freezing the application...")
    with c.cd(str(PROJECT_ROOT / "scripts" / "builder")):
        if app.get_version_info()["pre_type"] is None:
            print(
                "Final release detected. Python optimizations are currently disabled "
                "to ensure assert statements and runtime checks are preserved."
                " This is a temporary measure, and we plan to enable optimizations in future versions."
            )
            # TODO: Python optimization mode is commented out to prevent removal of assert statements
            # in production builds. Assert statements are crucial for ensuring runtime checks,
            # and omitting them could lead to unexpected behavior or failures.
            # To revisit: Determine how to handle optimizations without impacting critical runtime checks.
            # os.environ["PYTHONOPTIMIZE"] = "2"
        c.run(
            f"pyinstaller Bookworm.spec --clean -y --distpath {c['build_folder'].parent}",
            hide=False,
        )
        # This is required because pyxpdf_data looks for a default.xpdf file inside the site-packages folder
        # TODO: Fix this if at all possible
        lib = c["build_folder_content"] / "Lib" / "site-packages"
        os.makedirs(str(lib))
    print("App freezed.")


@task
@make_env
def copy_executables(c):
    if sys.platform == "win32":
        print("Copying antiword executable")
        build_folder = c["build_folder_content"]
        antiword_executable_dir = PROJECT_ROOT / "scripts" / "executables" / "antiword"
        antiword_dst = build_folder / "antiword"
        shutil.copytree(antiword_executable_dir, antiword_dst, dirs_exist_ok=True)
    print("Done copying executables.")


@task(
    pre=(freeze,),
    post=(copy_executables, make_installer, bundle_update),
)
@make_env
def build(c):
    """Freeze, package, and prepare the app for distribution."""
    # The following fixes a bug on windows where some DLL's are  not
    # deletable due to pyinstaller copying them
    # without clearing their read-only status
    if sys.platform == "win32":
        build_folder = Path(c["build_folder"])
        for dll_file in build_folder.glob("*.dll"):
            os.system(f"attrib -R {os.fspath(dll_file)}")


@task(name="create-portable")
@make_env
def create_portable_copy(c):
    from bookworm.utils import recursively_iterdir

    print("Creating portable archive...")
    env = os.environ
    frozen_dir = Path(env["IAPP_FROZEN_DIRECTORY"])
    fname = f"{env['IAPP_DISPLAY_NAME']}-{env['IAPP_VERSION']}-{env['IAPP_ARCH']}-portable.zip"
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


@task
@make_env
def bench(c, filename="tests/assets/epub30-spec.epub", runs=5):
    if shutil.which("hyperfine") is None:
        print(
            "To run this command, you need first to install hyperfine from the following URL:\n"
            "https://github.com/sharkdp/hyperfine/releases/latest"
        )
        return
    arch = os.environ["IAPP_ARCH"]
    c.run(
        f"hyperfine -N -r {runs} -w 1 "
        f'--export-json "scripts\\benchmark-{arch}.json" '
        f'"python -m bookworm benchmark {filename}"'
    )


@task(name="run")
def run_application(c, debug=True):
    """Runs the app."""
    try:
        # Ensure we import from source not from an installed package
        import bookworm

        if Path(bookworm.__path__[0]).parent != Path.cwd():
            print(
                "WARNING: bookworm is being imported from a different location.\n"
                "This may happen because bookworm is not installed in dev mode.\n"
                "Changes you make in the bookworm pacakge will not show up.\n"
                "To fix this, run:\n\tpip uninstall bookworm\n\tpip install -e .\n"
            )
        args = subprocess.list2cmdline(["--debug" if debug else ""])
        c.run(f"python -m bookworm {args}")
    except UnexpectedExit as e:
        exit(e.result.return_code)
