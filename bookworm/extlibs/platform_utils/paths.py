import inspect
import platform
import os
import subprocess
import sys
import string
import unicodedata

plat = platform.system()
is_windows = plat == "Windows"
is_mac = plat == "Darwin"
is_linux = plat == "Linux"

# ugly little monkeypatch to make the winpaths module work on Python 3
if is_windows:
    import ctypes
    import ctypes.wintypes

    ctypes.wintypes.create_unicode_buffer = ctypes.create_unicode_buffer
    import winpaths

try:
    unicode
except NameError:
    unicode = str


def app_data_path(app_name=None):
    """Cross-platform method for determining where to put application data."""
    """Requires the name of the application"""
    if is_windows:
        path = winpaths.get_appdata()
    elif is_mac:
        path = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    elif is_linux:
        path = os.path.expanduser("~")
        app_name = ".%s" % app_name.replace(" ", "_")
    return os.path.join(path, app_name)


def prepare_app_data_path(app_name):
    """Creates the application's data directory, given its name."""
    dir = app_data_path(app_name)
    return ensure_path(dir)


def embedded_data_path():
    if is_mac and is_frozen():
        return os.path.abspath(os.path.join(executable_directory(), "..", "Resources"))
    return app_path()


def is_frozen():
    """Return a bool indicating if application is compressed"""
    return hasattr(sys, "frozen")


def get_executable():
    """Returns the full executable path/name if frozen, or the full path/name of the main module if not."""
    if is_frozen():
        if not is_mac:
            return sys.executable
        # On Mac, sys.executable points to python. We want the full path to the exe we ran.
        exedir = os.path.abspath(os.path.dirname(sys.executable))
        items = os.listdir(exedir)
        items.remove("python")
        return os.path.join(exedir, items[0])
        # Not frozen
    try:
        import __main__

        return os.path.abspath(__main__.__file__)
    except AttributeError:
        return sys.argv[0]


def get_module(level=2):
    """Hacky method for deriving the caller of this function's module."""
    return inspect.getmodule(inspect.stack()[level][0]).__file__


def executable_directory():
    """Always determine the directory of the executable, even when run with py2exe or otherwise frozen"""
    executable = get_executable()
    path = os.path.abspath(os.path.dirname(executable))
    return path


def app_path():
    """Return the root of the application's directory"""
    path = executable_directory()
    if is_frozen() and is_mac:
        path = os.path.abspath(os.path.join(path, "..", ".."))
    return path


def module_path(level=2):
    return os.path.abspath(os.path.dirname(get_module(level)))


def documents_path():
    """On windows, returns the path to My Documents. On OSX, returns the user's Documents folder. For anything else, returns the user's home directory."""
    if is_windows:
        path = winpaths.get_my_documents()
    elif is_mac:
        path = os.path.join(os.path.expanduser("~"), "Documents")
    else:
        path = os.path.expanduser("~")
    return path


def safe_filename(filename):
    """Given a filename, returns a safe version with no characters that would not work on different platforms."""
    SAFE_FILE_CHARS = "'-_.()[]{}!@#$%^&+=`~ "
    filename = unicode(filename)
    new_filename = "".join(c for c in filename if c in SAFE_FILE_CHARS or c.isalnum())
    # Windows doesn't like directory names ending in space, macs consider filenames beginning with a dot as hidden, and windows removes dots at the ends of filenames.
    return new_filename.strip(" .")


def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def start_file(path):
    if is_windows:
        os.startfile(path)
    else:
        subprocess.Popen(["open", path])


def get_applications_path():
    """Return the directory where applications are commonly installed on the system."""
    if is_windows:
        return winpaths.get_program_files()
    elif is_mac:
        return "/Applications"
