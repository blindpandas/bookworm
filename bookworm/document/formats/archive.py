# coding: utf-8

from __future__ import annotations
import os
import contextlib
import uuid
from functools import cached_property
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from bookworm import app
from bookworm.runtime import PackagingMode, CURRENT_PACKAGING_MODE
from bookworm.paths import app_path
from bookworm.logger import logger
from .. import (
    DummyDocument,
    ChangeDocument,
    DocumentCapability as DC,
    DocumentIOError,
    DocumentEncryptedError,
    ArchiveContainsMultipleDocuments,
    ArchiveContainsNoDocumentsError,
)
from ..uri import DocumentUri

log = logger.getChild(__name__)


if not app.is_frozen:
    unrar_dll_dir = Path.cwd() / "scripts" / "dlls" / "unrar_dll"
else:
    unrar_dll_dir = app_path("unrar_dll")
unrar_dll = os.path.join(
    unrar_dll_dir,
    "UnRAR.dll" if app.arch == "x86" else "UnRAR64.dll"
)
os.environ["UNRAR_LIB_PATH"] = unrar_dll

from unrar.rarfile import RarFile

class ArchivedDocument(DummyDocument):

    format = "archive"
    # Translators: the name of a document file format
    name = _("Archive File")
    extensions = ("*.zip", "*.rar")
    capabilities = DC.ASYNC_READ
    archive_handlers = {
        '.zip': ZipFile,
        '.rar': RarFile,
    }

    def read(self):
        self.archive = self._open_archive(self.get_file_system_path())
        self.decryption_key = self.uri.view_args.get("decryption_key")
        self._temp_extraction_directory = None
        arch_prefix, file_list = self.archive_namelist
        if not file_list:
            raise ArchiveContainsNoDocumentsError
        elif (member := self.uri.view_args.get('member')):
            self.open_member_as_document(member)
        elif len(file_list) == 1:
            self.open_member_as_document(file_list[0])
        elif len(file_list) > 1:
            raise ArchiveContainsMultipleDocuments(file_list)

    def close(self):
        super().close()
        self.archive.close()
        if self._temp_extraction_directory is not None:
            self._temp_extraction_directory.cleanup()

    @cached_property
    def archive_namelist(self) -> tuple[str, list]:
        supported_exts = self.get_supported_file_extensions()
        namelist = tuple(filter(
            lambda fname: PurePosixPath(fname).suffix.lower() in supported_exts,
            self.archive.namelist()
        ))
        if (prefix := os.path.commonprefix(namelist)):
            return (
                prefix,
                [os.path.relpath(mem, prefix) for mem in namelist]
            )
        return ("", namelist)

    def open_member_as_document(self, member):
        self._temp_extraction_directory = TemporaryDirectory()
        extracted_file = self.extract_member(
            member,
            self._temp_extraction_directory
        )
        new_uri = DocumentUri.from_filename(extracted_file)
        new_uri.view_args['add_to_recents'] = False
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=new_uri,
            reason="Extracted member from the archive",
        )

    def _open_archive(self, filename):
        if (handler := self.archive_handlers.get(filename.suffix.lower())):
            return handler(os.fspath(filename), 'r')
        raise DocumentIOError(f"Unsupported archive format: {filename}")

    def extract_member(self, member_name, extraction_directory):
        full_member_path = Path(self.archive_namelist[0]).joinpath(Path(member_name))
        target_filename = Path(extraction_directory.name).joinpath(full_member_path)
        target_filename.parent.mkdir(parents=True, exist_ok=True)
        pwd = (
            self.decryption_key.encode("utf-8")
            if self.decryption_key is not None
            else None
        )
        with open(target_filename, "wb") as outfile:
            try:
                with self.archive.open(full_member_path.as_posix(), pwd=pwd) as infile:
                    for chunk in infile:
                        outfile.write(chunk)
            except RuntimeError as e:
                if "password" in e.args[0]:
                    raise DocumentEncryptedError(self)
                raise
        return target_filename
