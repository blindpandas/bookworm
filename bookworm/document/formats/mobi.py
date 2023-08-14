# coding: utf-8

from __future__ import annotations

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import mobi

from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from bookworm.paths import home_data_path
from bookworm.utils import generate_file_md5, mute_stdout

from .. import ChangeDocument
from .. import DocumentCapability as DC
from .. import DocumentError, DummyDocument

log = logger.getChild(__name__)
CONTAINER_XML = """
<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>
""".strip()
EPUB_STRUCTURE_FILES = {
    "mimetype": "application/epub+zip",
    "META-INF/container.xml": CONTAINER_XML,
}


class MobiDocument(DummyDocument):
    format = "mobi"
    # Translators: the name of a document file format
    name = _("Kindle eBook")
    extensions = (
        "*.mobi",
        "*.azw3",
    )
    capabilities = DC.ASYNC_READ

    def __len__(self):
        raise NotImplementedError

    def get_page(self, index):
        raise NotImplementedError

    def read(self):
        mobi_file_path = self.get_file_system_path()
        unpacked_file_path = self.unpack_mobi(mobi_file_path)
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(unpacked_file_path),
            reason="Unpacked the mobi file to epub",
        )

    def unpack_mobi(self, filename):
        storage_area = self.get_mobi_storage_area()
        filemd5 = generate_file_md5(filename)
        for fname in storage_area.iterdir():
            if fname.is_file() and (fname.stem == filemd5):
                return str(fname)
        with mute_stdout():
            tempdir, extracted_file = mobi.extract(str(filename))
        filetype = Path(extracted_file).suffix.strip(".")
        if filetype == "html":
            return self.create_valid_epub_from_epub_like_structure(
                tempdir, storage_area.joinpath(f"{filemd5}.epub")
            )
        dst_filename = storage_area.joinpath(f"{filemd5}.{filetype}")
        shutil.copy(extracted_file, dst_filename)
        TemporaryDirectory._rmtree(tempdir)
        return dst_filename

    @classmethod
    def get_mobi_storage_area(cls):
        storage_area = home_data_path("unpacked_mobi")
        if not storage_area.exists():
            storage_area.mkdir(parents=True, exist_ok=True)
        return storage_area

    @classmethod
    def create_valid_epub_from_epub_like_structure(cls, src_folder, dst_file):
        inner_mobi_folder = tuple(
            filter(lambda fd: fd.lower().startswith("mobi"), os.listdir(src_folder))
        )
        if not inner_mobi_folder:
            raise RuntimeError("Unrecognized EPUB like structure")
        src_epub_folder = Path(src_folder, inner_mobi_folder[0])
        files_to_write = [
            (fname, content)
            for fname, content in EPUB_STRUCTURE_FILES.items()
            if not Path(src_epub_folder, fname).exists()
        ]
        for fname, content in files_to_write:
            file = Path(src_epub_folder, fname)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(content)
        ziparchive_filename = Path(
            shutil.make_archive(dst_file, "zip", src_epub_folder)
        )
        created_epub_filename = ziparchive_filename.with_suffix("")
        ziparchive_filename.rename(created_epub_filename)
        return created_epub_filename
