# coding: utf-8

import os
import sys
from dataclasses import dataclass
from functools import wraps
from typing import Iterable

from bookworm import app
from bookworm.logger import logger
from bookworm.shellinfo import get_ext_info
from bookworm.utils import ignore

from . import shellapi
from .win_registry import RegValueType, RegKey

log = logger.getChild(__name__)


EXECUTABLE = sys.executable


def add_shell_command(key, executable):
    key.create_subkey(r"shell\Open\Command").set_value(
        "", f'"{executable}" "launcher" "%1"'
    )



def shell_notify_association_changed():
    shellapi.SHChangeNotify(
        shellapi.SHCNE_ASSOCCHANGED, shellapi.SHCNF_IDLIST, None, None
    )


def register_application(prog_id, executable, supported_exts):
    exe = os.path.split(executable)[-1]
    with RegKey.LocalSoftware(rf"Applications\{exe}", ensure_created=True) as exe_key:
        add_shell_command(exe_key, executable)
        with RegKey(exe_key, "SupportedTypes", ensure_created=True) as supkey:
            for ext in get_ext_info(supported_exts):
                supkey.set_value(ext, "")


def associate_extension(ext, prog_id, executable, desc, icon=None):
    # Add the prog_id
    with RegKey.LocalSoftware(prog_id, ensure_created=True) as progkey:
        progkey.set_value("", desc)
        with RegKey(progkey, "DefaultIcon", ensure_created=True) as iconkey:
            iconkey.set_value("", icon or executable)
        add_shell_command(progkey, executable)
    # Associate file type
    with RegKey.LocalSoftware(rf"{ext}\OpenWithProgids", ensure_created=True) as askey:
        askey.set_value(prog_id, b"", RegValueType.BYTES)
    # Set this executable as the default handler for files with this extension
    with RegKey.LocalSoftware(ext, ensure_created=True) as defkey:
        defkey.set_value("", prog_id)


def remove_association(ext, prog_id):
    try:
        progkey = RegKey.LocalSoftware(prog_id)
    except OSError:
        log.warning(f"Faild to remove the prog_id key for {prog_id}")
    else:
        progkey.delete_key_tree()
    try:
        extkey = RegKey.LocalSoftware(rf"{ext}\OpenWithProgids")
        extkey.delete_value(prog_id)
    except OSError:
        log.warning(f"Faild to remove the openwith value for ext {ext}")
    try:
        root_extkey = RegKey.LocalSoftware(ext)
        root_extkey.set_value("", "")
    except OSError:
        log.warning(f"Faild to remove the default ext key for ext {ext}")




@ignore(Exception)
def shell_integrate(supported="*"):
    if not app.is_frozen:
        return log.warning(
            "File association is not available when running from source."
        )
    log.info(f"Registering file associations for extensions {supported}.")
    register_application(app.prog_id, EXECUTABLE, supported)
    doctypes = get_ext_info(supported)
    for (ext, (prog_id, desc, icon)) in doctypes.items():
        associate_extension(ext, prog_id, EXECUTABLE, desc, icon)
    shell_notify_association_changed()


@ignore(Exception)
def shell_disintegrate(supported="*"):
    if not app.is_frozen:
        log.warning("File association is not available when running from source.")
        return
    log.info(f"Unregistering file associations for extensions {supported}.")
    exe = os.path.split(EXECUTABLE)[-1]
    try:
        exekey = RegKey.LocalSoftware(fr"Applications\{exe}", writable=True)
    except OSError:
        log.warning(f"Could not open Applications key")
    else:
        exekey.delete_key_tree()
    doctypes = get_ext_info(supported)
    for (ext, (prog_id, desc, icon)) in doctypes.items():
        remove_association(ext, prog_id)
    shell_notify_association_changed()
