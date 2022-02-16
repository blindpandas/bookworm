# coding: utf-8

"""Utilities to facilitate working with the Windows Registry."""

from dataclasses import dataclass

import System
from Microsoft.Win32 import Registry, RegistryKey, RegistryValueKind


@dataclass
class RegKey:
    """Represent a key in the windows registry."""

    root: RegistryKey
    path: str
    writable: bool = True
    ensure_created: bool = False

    def __post_init__(self):
        self.key = self.root.OpenSubKey(self.path, self.writable)
        if self.key is None and self.ensure_created:
            self.create()

    def close(self):
        if self.key is not None:
            self.key.Close()
            self.key.Dispose()

    @property
    def exists(self):
        return self.key is not None

    def create(self):
        self.key = self.root.CreateSubKey(self.path)

    def __getattr__(self, attr):
        if self.key is None:
            raise LookupError(f"Key {self!r} does not exists.")
        return getattr(self.key, attr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @classmethod
    def LocalSoftware(cls, *args, **kwargs):
        root = cls(
            Registry.CurrentUser, r"SOFTWARE\Classes", kwargs.pop("writable", True)
        )
        return cls(root, *args, **kwargs)
