# coding: utf-8

from __future__ import annotations

from mistune import markdown

from bookworm.document.uri import DocumentUri
from bookworm.logger import logger
from bookworm.paths import home_data_path
from bookworm.utils import generate_file_md5

from .. import ChangeDocument
from .. import DocumentCapability as DC
from .. import DocumentEncryptedError, DocumentError, DummyDocument

log = logger.getChild(__name__)


class MarkdownDocument(DummyDocument):

    format = "markdown"
    # Translators: the name of a document file format
    name = _("Markdown File")
    extensions = ("*.md",)

    def read(self):
        self.filename = self.get_file_system_path()
        rendered_md_path = home_data_path("rendered_markdown")
        rendered_md_path.mkdir(parents=True, exist_ok=True)
        filehash = generate_file_md5(self.filename)
        target_file = rendered_md_path / f"{filehash}.html"
        html_content = markdown(self.filename.read_text(), escape=False)
        target_file.write_text(html_content)
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(target_file),
            reason="Unpacked the mobi file to epub",
        )
