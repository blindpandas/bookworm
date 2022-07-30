# coding: utf-8

"""Utilities to facilitate working with the Windows Registry."""

import os
import winreg
from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from bookworm import typehints as t



class RegValueType(Enum):
    NONE = None
    INTEGER = int
    STRING = str
    REG_EXPAND_SZ = winreg.REG_EXPAND_SZ
    BYTES = bytes

    @cached_property
    def _winreg_conversion_table(self):
        return {
            RegValueType.NONE: winreg.REG_NONE,
            RegValueType.STRING: winreg.REG_SZ,
            RegValueType.REG_EXPAND_SZ: winreg.REG_EXPAND_SZ,
            RegValueType.INTEGER: winreg.REG_DWORD,
            RegValueType.BYTES: winreg.REG_BINARY,
        }

    def _as_winreg_regtype(self):
        return self._winreg_conversion_table[self]


class RegRoots:
    __slots__ = []

    LocalMachine = winreg.HKEY_LOCAL_MACHINE
    ClassesRoot = winreg.HKEY_CLASSES_ROOT
    CurrentUser = winreg.HKEY_CURRENT_USER
    CurrentConfig = winreg.HKEY_CURRENT_CONFIG
    Users = winreg.HKEY_USERS


@dataclass
class RegKey:
    """Represents a key in the windows registry."""

    root: t.ForwardRef("RegKey")
    path: str
    writable: bool = True
    ensure_created: bool = False

    def __post_init__(self):
        if isinstance(self.root, RegKey):
            self.path = os.path.join(self.root.path, self.path)
            self.root = self.root.root
        if self.writable:
            self.key_flags = winreg.KEY_READ | winreg.KEY_WRITE
        else:
            self.key_flags = winreg.KEY_READ
        key = None
        try:
            key = winreg.OpenKeyEx(self.root, self.path)
        except FileNotFoundError:
            if self.ensure_created:
                self.create()
            else:
                raise FileNotFoundError(f"Registry key not found: root={self.root}, path={self.path}")
        self.create()

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.key.Close()
        except:
            pass

    @property
    def exists(self):
        try:
            winreg.OpenKeyEx(self.root, self.path)
        except FileNotFoundError:
            return False
        return True

    @property
    def num_subkeys(self):
        return winreg.QueryInfoKey(self.key)[0]

    @property
    def num_values(self):
        return winreg.QueryInfoKey(self.key)[1]

    def get_parent_key(self, *, writable=False):
        return RegKey(root=self.root, path="", writable=writable)

    def create(self):
        self.key = winreg.CreateKeyEx(self.root, self.path, access=self.key_flags)

    def create_subkey(self, keyname):
        winreg.CreateKeyEx(self.key, keyname, access=winreg.KEY_WRITE)
        return RegKey(root=self, path=keyname, writable=self.writable)

    def get_value(self, valuename):
        return winreg.QueryValueEx(self.key, valuename)[0]

    def set_value(self, valuename, valuedata, valuetype=RegValueType.STRING):
        winreg.SetValueEx(self.key, valuename, 0, RegValueType(valuetype)._as_winreg_regtype(), valuedata)

    def delete_value(self, valuename):
        winreg.DeleteValue(self.key, valuename)

    def is_subkey(self, other):
        return os.path.join(str(other.root), other.path).strip("\\").startswith(
            os.path.join(str(self.root), self.path).strip("\\")
        )

    def delete_subkey(self, subkey):
        if isinstance(subkey, str):
            try:
                subkey = RegKey(root=self, path=subkey, writable=True)
            except FileNotFoundError:
                raise FileNotFoundError(f"Subkey {subkey} not found.")

        assert self.is_subkey(subkey), "Should be a subkey of this key"

        def _del_key_and_subkeys_recursive(root):
            for sbkey in root.iter_subkeys(writable=True):
                _del_key_and_subkeys_recursive(sbkey)
            try:
                winreg.DeleteKey(root.root, root.path)
            except OSError:
                pass

        _del_key_and_subkeys_recursive(subkey)

    def delete_key_tree(self):
        for subkey in self.iter_subkeys(writable=True):
            self.delete_subkey(subkey)
        self.get_parent_key(writable=True).delete_subkey(self)

    def iter_subkeys(self, *, writable=None):
        index = 0
        writable = writable if (writable is not None) else self.writable
        while True:
            try:
                yield RegKey(
                    root=self,
                    path=winreg.EnumKey(self.key, index),
                    writable=writable
                )
            except OSError:
                break
            else:
                index += 1

    def iter_values(self):
        index = 0
        while True:
            try:
                valuename, valuedata, valuetype = winreg.EnumValue(self.key, index)
            except OSError:
                break
            else:
                yield (valuename, valuedata)
                index += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def LocalSoftware(cls, *args, **kwargs):
        root = cls(
            RegRoots.CurrentUser, r"SOFTWARE\Classes", kwargs.pop("writable", True)
        )
        return cls(root, *args, **kwargs)
