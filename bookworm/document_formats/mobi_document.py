# coding: utf-8

import os
import shutil
from hashlib import md5
from tempfile import TemporaryDirectory
from pathlib import Path
from bookworm.paths import home_data_path
from bookworm.document_uri import DocumentUri
from bookworm.utils import mute_stdout
from bookworm.document_formats.base import (
    BaseDocument,
    ChangeDocument,
    DocumentError,
    DocumentEncryptedError
)
from bookworm.vendor.KindleUnpack import kindleunpack as KindleUnpack
from bookworm.logger import logger
from.epub_document import EpubDocument


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
    'mimetype': 'application/epub+zip',
    'META-INF/container.xml': CONTAINER_XML,
}

class MobiDocument(EpubDocument):

    format = "mobi"
    # Translators: the name of a document file format
    name = _("Mobi Book")
    extensions = ("*.mobi", "*.azw3", "*.azw4")

    def read(self):
        mobi_file_path = self.get_file_system_path()
        epub_file_path = self.unpack_mobi_and_get_epub(mobi_file_path)
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(epub_file_path),
            reason="Unpacked the mobi file to epub",
        )

    def unpack_mobi_and_get_epub(self, filename):
        hasher = md5()
        for chunk in open(filename, "rb"):
            hasher.update(chunk)
        filemd5 = hasher.hexdigest()
        epub_filename = home_data_path(f"{filemd5}.epub")
        if epub_filename.is_file():
            return epub_filename
        with TemporaryDirectory() as tempdir:
            extraction_dir = os.path.join(tempdir, filemd5)
            with mute_stdout():
                KindleUnpack.unpackBook(str(filename), extraction_dir)
            zip_dir = os.path.join(extraction_dir, 'mobi7')
            if not os.path.isdir(zip_dir):
                zip_dir = os.path.join(extraction_dir, 'mobi8')
            for fname, content in EPUB_STRUCTURE_FILES.items():
                file = Path(zip_dir, fname)
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text(content)
            ziparchive_filename = Path(shutil.make_archive(epub_filename, 'zip', zip_dir))
            created_epub_filename = ziparchive_filename.with_suffix("")
            ziparchive_filename.rename(created_epub_filename)
            return created_epub_filename
