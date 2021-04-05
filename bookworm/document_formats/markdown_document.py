# coding: utf-8

from hashlib import md5
from pathlib import Path
from mistune import markdown
from bookworm.paths import home_data_path
from bookworm.utils import generate_sha1hash
from bookworm.document_uri import DocumentUri
from bookworm.document_formats.base import (
    BaseDocument,
    ChangeDocument,
    DocumentError,
)
from bookworm.logger import logger


log = logger.getChild(__name__)


class MarkdownDocument(BaseDocument):

    format = "markdown"
    # Translators: the name of a document file format
    name = _("Markdown File")
    extensions = ("*.md",)

    def __len__(self):
        raise NotImplementedError

    def get_page(self, index):
        raise NotImplementedError

    def read(self):
        self.filename = self.get_file_system_path()
        rendered_md_path = home_data_path("rendered_markdown")
        rendered_md_path.mkdir(parents=True, exist_ok=True)
        filehash = generate_sha1hash(self.filename)
        target_file = rendered_md_path / f"{filehash}.html"
        html_content = markdown(self.filename.read_text(), escape=False)
        target_file.write_text(html_content)
        raise ChangeDocument(
            old_uri=self.uri,
            new_uri=DocumentUri.from_filename(target_file),
            reason="Unpacked the mobi file to epub",
        )

    @property
    def toc_tree(self):
        raise NotImplementedError

    @property
    def metadata(self):
        raise NotImplementedError
