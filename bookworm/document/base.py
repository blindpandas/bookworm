
from __future__ import annotations

import gc
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Sequence
from functools import cached_property, lru_cache
from pathlib import Path

import pywhatlang
from blake3 import blake3
from more_itertools import flatten
from selectolax.parser import HTMLParser

from bookworm import typehints as t
from bookworm.concurrency import QueueProcess
from bookworm.i18n import LocaleInfo
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.structured_text import (
    CURRENT_CONTENT_HASH_VERSION,
    SemanticElementType,
    TEXT_OBJECT_REPLACEMENT_CHAR,
    TextPositionMap,
    TextRange,
)
from bookworm.utils import (
    get_url_spans,
    remove_excess_blank_lines,
)

from . import operations as doctools
from .elements import *
from .exceptions import DocumentIOError
from .features import DocumentCapability, ReadingMode

log = logger.getChild(__name__)
PAGE_CACHE_CAPACITY = 300


class BaseDocument(Sequence, Iterable, metaclass=ABCMeta):
    """Defines the core interface of a document."""

    __internal__ = False
    """A flag to indicate whether this type of document is visible to the user."""

    format: str = None
    """The developer oriented format of this document."""

    name: str = None
    """The displayable name of this document format."""

    extensions: t.Tuple[str] = None
    """The file extension(s) of this format."""

    capabilities: DocumentCapability = DocumentCapability.NULL_CAPABILITY
    """A combination of DocumentCapability flags."""

    supported_reading_modes: t.Tuple[ReadingMode] = (ReadingMode.DEFAULT,)
    default_reading_mode: ReadingMode = ReadingMode.DEFAULT

    document_classes: dict[str, t.ForwardRef("BaseDocument")] = {}
    """A dict of subclasses representing supported document types."""

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if (cls.format is not None) and cls.check():
            cls.document_classes[cls.format.lower()] = cls

    @classmethod
    def get_document_class_given_format(cls, format: str) -> BaseDocument:
        return cls.document_classes.get(format.lower())

    @classmethod
    def get_supported_file_extensions(cls):
        exts = flatten(
            doc_cls.extensions
            for doc_cls in cls.document_classes.values()
            if doc_cls.extensions is not None
        )
        return frozenset(ext.lstrip("*") for ext in exts)

    @classmethod
    def check(cls) -> bool:
        """Return True if this document format is supported based on the user's environment."""
        return True

    def __init__(self, uri):
        self.uri = uri
        self._is_read = False

    def __contains__(self, value: int) -> bool:
        return -1 < value < len(self)

    def __getitem__(self, index: int) -> BasePage:
        return self.get_page(index)

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __getstate__(self) -> dict:
        """Support for pickling."""
        return dict(uri=self.uri)

    def __setstate__(self, state: dict) -> None:
        """Support for unpickling."""
        self.__dict__.update(state)
        self.read()

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}: "
            f"format={self.format}, "
            f"capabilities={self.capabilities!r}, "
            f"uri={self.uri!r}"
            ">"
        )

    @cached_property
    def reading_options(self) -> ReadingOptions:
        reading_mode = int(self.uri.openner_args.get("reading_mode", ReadingMode.DEFAULT))
        return ReadingOptions(
            reading_mode=ReadingMode(reading_mode),
        )

    @cached_property
    def identifier(self) -> str:
        """Return a unique identifier for this document."""
        return self.uri.to_uri_string()

    @abstractmethod
    def read(self) -> None:
        """
        Perform the actual IO operations for loading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        self._is_read = True

    @staticmethod
    def _has_hashable_text(text: str) -> bool:
        return bool(text.replace(TEXT_OBJECT_REPLACEMENT_CHAR, "").strip())

    def iter_content_hash_images(self):
        return ()

    @staticmethod
    def _hash_document_text(text: str) -> str | None:
        normalized_text = text.strip()
        if not BaseDocument._has_hashable_text(normalized_text):
            return None
        return blake3(normalized_text.encode()).hexdigest()

    @staticmethod
    def _update_content_hash_segment(hasher, kind: str, payload: bytes) -> None:
        encoded_kind = kind.encode()
        hasher.update(len(encoded_kind).to_bytes(2, "big"))
        hasher.update(encoded_kind)
        hasher.update(len(payload).to_bytes(8, "big"))
        hasher.update(payload)

    @classmethod
    def _hash_document_pages_with_images(cls, pages) -> tuple[str | None, bool]:
        has_meaningful_text = False
        has_images = False
        legacy_hasher = blake3()
        page_records = []
        for page_index, page in enumerate(pages):
            storage_text = page.get_storage_text() or ""
            encoded_text = storage_text.encode()
            if cls._has_hashable_text(storage_text):
                has_meaningful_text = True
            legacy_hasher.update(len(encoded_text).to_bytes(8, "big"))
            legacy_hasher.update(encoded_text)
            page_records.append((page_index, storage_text, page))
        if not has_meaningful_text:
            return None, False
        structured_hasher = blake3()
        structured_hasher.update(
            f"bookworm-content-hash-v{CURRENT_CONTENT_HASH_VERSION}".encode()
        )
        has_unresolved_images = False
        for page_index, storage_text, page in page_records:
            encoded_text = storage_text.encode()
            cls._update_content_hash_segment(
                structured_hasher,
                "page",
                page_index.to_bytes(8, "big"),
            )
            image_segments = sorted(
                tuple(page.iter_content_hash_images()),
                key=lambda segment: (segment[0].start, segment[0].stop),
            )
            if not image_segments:
                cls._update_content_hash_segment(structured_hasher, "text", encoded_text)
                continue
            has_images = True
            cursor = 0
            text_length = len(storage_text)
            for storage_range, image_identity in image_segments:
                start = min(max(storage_range.start, 0), text_length)
                stop = min(max(storage_range.stop, start), text_length)
                if start < cursor:
                    continue
                cls._update_content_hash_segment(
                    structured_hasher,
                    "text",
                    storage_text[cursor:start].encode(),
                )
                if image_identity is None:
                    has_unresolved_images = True
                else:
                    kind, payload = image_identity
                    cls._update_content_hash_segment(
                        structured_hasher,
                        f"image:{kind}",
                        payload,
                    )
                cursor = stop
            cls._update_content_hash_segment(
                structured_hasher,
                "text",
                storage_text[cursor:].encode(),
            )
        if has_unresolved_images:
            return None, has_images
        if not has_images:
            return legacy_hasher.hexdigest(), False
        return structured_hasher.hexdigest(), True

    def get_content_hash(self) -> str | None:
        """
        Generates the content hash for this document
        subclasses may override this if necessary, such as in the case of SinglePageDocument
        """
        if hasattr(self, "_content_hash"):
            return self._content_hash
        if not self._is_read:
            self.read()
        content_hash, has_images = self._hash_document_pages_with_images(self)
        self._content_hash = content_hash
        self._content_hash_has_images = has_images
        if not has_images:
            self._legacy_content_hash = content_hash
        return self._content_hash

    def _cache_legacy_content_hash_if_possible(self) -> bool:
        if hasattr(self, "_legacy_content_hash"):
            return True
        if (
            hasattr(self, "_content_hash")
            and getattr(self, "_content_hash_has_images", None) is False
        ):
            self._legacy_content_hash = self._content_hash
            return True
        return False

    @classmethod
    def _hash_legacy_document_pages(cls, pages) -> str | None:
        """Hash the pre-image-navigation visible text used by older records."""
        has_meaningful_text = False
        hasher = blake3()
        for page in pages:
            display_text = page.get_legacy_text() or ""
            if cls._has_hashable_text(display_text):
                has_meaningful_text = True
            encoded_text = display_text.encode()
            hasher.update(len(encoded_text).to_bytes(8, "big"))
            hasher.update(encoded_text)
        if not has_meaningful_text:
            return None
        return hasher.hexdigest()

    def get_legacy_content_hash(self) -> str | None:
        """Return the pre-storage-map hash used by older database records."""
        if self._cache_legacy_content_hash_if_possible():
            return self._legacy_content_hash
        if not self._is_read:
            self.read()
        self._legacy_content_hash = self._hash_legacy_document_pages(self)
        return self._legacy_content_hash

    def close(self) -> None:
        """Perform the actual IO operations for unloading the ebook.
        Subclasses should call super to ensure the standard behavior.
        """
        self._is_read = False
        gc.collect()

    @abstractmethod
    def get_page(self, index: int) -> BasePage:
        """Return the page object at index."""

    def get_page_number_from_page_label(self, page_label):
        if DocumentCapability.PAGE_LABELS not in self.capabilities:
            raise NotImplementedError("This feature is not enabled for this class of documents")
        for page in self:
            page_label = page_label.lower()
            if page.get_label().lower() == page_label:
                return page
        raise LookupError(f"Failed to find a page with the label {page_label}.")

    @property
    @abstractmethod
    def toc_tree(self) -> t.Iterable[Section]:
        """Return an iterable representing the table of content.
        The items should be of type `Section`.
        """

    @cached_property
    def language(self) -> str:
        num_pages = len(self)
        num_samples = num_pages if num_pages <= 20 else 20
        text = "".join(self[i].get_text() for i in range(num_samples))
        return self.get_language(samples=text, is_html=False)

    @property
    @abstractmethod
    def metadata(self) -> BookMetadata:
        """Return a `BookMetadata` object holding info about this book."""

    @lru_cache(maxsize=1000)
    def get_page_content(self, page_number: int) -> str:
        """Convenience method: return the text content of a page."""
        return self[page_number].get_text()

    def get_page_image(self, page_number: int, zoom_factor: float = 1.0) -> ImageIO:
        """Convenience method: return the image of a page."""
        return self[page_number].get_image(zoom_factor)

    def get_cover_image(self) -> t.Optional[ImageIO]:
        """Return the cover image of this document."""

    def get_file_system_path(self):
        """Only valid for documents that have true filesystem path."""
        if (filepath := Path(self.uri.path)).exists():
            return filepath
        raise DocumentIOError(f"File {filepath} does not exist.")

    @classmethod
    def should_read_async(cls):
        return DocumentCapability.ASYNC_READ in cls.capabilities

    @classmethod
    def uses_chapter_by_chapter_navigation_model(self):
        return self.default_reading_mode is ReadingMode.CHAPTER_BASED

    @classmethod
    def supports_structural_navigation(cls):
        return DocumentCapability.STRUCTURED_NAVIGATION in cls.capabilities

    @classmethod
    def supports_links(cls):
        return (
            DocumentCapability.LINKS in cls.capabilities
            or DocumentCapability.INTERNAL_ANCHORS in cls.capabilities
        )

    @classmethod
    def is_single_page_document(cls):
        return DocumentCapability.SINGLE_PAGE in cls.capabilities

    @classmethod
    def has_toc_tree(self):
        return DocumentCapability.TOC_TREE in self.capabilities

    @classmethod
    def can_render_pages(self):
        return DocumentCapability.GRAPHICAL_RENDERING in self.capabilities

    @staticmethod
    def get_language(samples, is_html=False, hint_language: str = "en") -> LocaleInfo:
        """Return the language of this document.
        By default we use a heuristic based on whatlang.
        """
        if is_html:
            samples = HTMLParser(samples).text()
        try:
            lang_code, confidence, is_reliable = pywhatlang.detect_lang(samples)
        except:
            log.error("Failed to recognize document language", exc_info=True)
        else:
            return LocaleInfo(lang_code).parent
        return LocaleInfo(hint_language)

    def export_to_text(self, target_filename: t.PathLike):
        return QueueProcess(
            target=doctools.export_to_plain_text,
            args=(self, target_filename),
            name="document-export",
        )

    def search(self, request: doctools.SearchRequest):
        yield from QueueProcess(
            target=doctools.search_book, args=(self, request), name="document-search"
        )


class BasePage(metaclass=ABCMeta):
    """Represents a page from the document."""

    __slots__ = ["document", "index"]

    def __init__(self, document: BaseDocument, index: int):
        self.document = document
        self.index = index

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.index}>"

    @abstractmethod
    def get_text(self) -> str:
        """Return the text content or raise NotImplementedError."""

    def get_storage_text(self) -> str:
        """Return stable text for hashes and persisted positions."""
        return self.get_text()

    def get_legacy_text(self) -> str:
        """Return the visible text model used before embedded image placeholders."""
        return self.get_text()

    def get_text_position_map(self) -> TextPositionMap:
        return TextPositionMap.identity(len(self.get_text()))

    def get_legacy_text_position_map(self) -> TextPositionMap:
        if hasattr(self, "_legacy_text_position_map"):
            return self._legacy_text_position_map
        legacy_text = self.get_legacy_text()
        storage_text = self.get_storage_text()
        self._legacy_text_position_map = TextPositionMap.from_texts(
            legacy_text,
            storage_text,
        )
        return self._legacy_text_position_map

    def iter_content_hash_images(self):
        return ()

    def display_to_storage_position(self, pos: int, affinity="before") -> int:
        return self.get_text_position_map().display_to_storage_position(pos, affinity=affinity)

    def storage_to_display_position(self, pos: int, affinity="before") -> int:
        return self.get_text_position_map().storage_to_display_position(pos, affinity=affinity)

    def display_to_storage_range(self, start: int, stop: int) -> TextRange:
        return self.get_text_position_map().display_to_storage_range(start, stop)

    def storage_to_display_range(self, start: int, stop: int) -> TextRange:
        return self.get_text_position_map().storage_to_display_range(start, stop)

    def legacy_to_storage_position(self, pos: int, affinity="before") -> int:
        return self.get_legacy_text_position_map().display_to_storage_position(
            pos,
            affinity=affinity,
        )

    def legacy_to_storage_range(self, start: int, stop: int) -> TextRange:
        return self.get_legacy_text_position_map().display_to_storage_range(start, stop)

    def get_image(self, zoom_factor: float) -> ImageIO:
        """
        Return page image as `ImageIO`
        or raise NotImplementedError.
        """
        raise NotImplementedError

    def get_embedded_image(self, image_index: int) -> ImageIO:
        """Return an image embedded in the page content."""
        raise NotImplementedError

    def get_embedded_image_info(self, image_index: int):
        """Return metadata for an image embedded in the page content."""
        raise NotImplementedError

    def get_label(self) -> str:
        """Return the page label string (commonly found on PDFs)."""
        return ""

    def get_semantic_structure(
        self,
    ) -> dict[SemanticElementType, list[tuple[int, int]]]:
        """Return information about the position of semantic elements."""
        raise NotImplementedError

    def get_style_info(self) -> dict[SemanticElementType, list[tuple[int, int]]]:
        """Return information about the position of styled elements."""
        raise NotImplementedError

    def resolve_link(self, link_range) -> LinkTarget:
        raise NotImplementedError

    def get_link_for_text_range(self, text_range) -> LinkTarget:
        retval = self.get_external_link_target(text_range)
        if retval is None:
            try:
                retval = self.resolve_link(text_range)
            except NotImplementedError:
                retval = None
        return retval

    @property
    def semantic_structure(self):
        try:
            semantic_structure = self.get_semantic_structure()
        except NotImplementedError:
            semantic_structure = {}
        semantic_link_ranges = semantic_structure.setdefault(SemanticElementType.LINK, [])
        all_link_ranges = [
            *semantic_link_ranges,
            *(
                text_range
                for (text_range, __url) in self.get_external_links()
                if text_range not in semantic_link_ranges
            ),
        ]
        semantic_structure[SemanticElementType.LINK] = all_link_ranges
        return semantic_structure

    def get_external_links(self) -> tuple[tuple[int, int], str]:
        return get_url_spans(self.get_text())

    def get_external_link_target(self, text_range) -> str:
        if url := dict(self.get_external_links()).get(text_range):
            return LinkTarget(url=url, is_external=True)

    def normalize_text(self, text):
        return remove_excess_blank_lines(text)

    @property
    def number(self) -> int:
        """The user facing page number."""
        return self.index + 1

    @cached_property
    def section(self) -> Section:
        """The (most specific) section that this page blongs to."""
        rv = self.document.toc_tree
        for sect in rv.iter_children():
            if self.index in sect.pager:
                rv = sect
                if sect.pager.first > self.index:
                    break
        return rv

    @property
    def is_first_of_section(self) -> bool:
        return self.index == self.section.pager.first

    @property
    def is_last_of_section(self) -> bool:
        return self.index == self.section.pager.last

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.document is other.document) and (self.index == other.index)
        return NotImplemented


class SinglePage(BasePage):
    """Emulates a page for a single page document."""

    def get_text(self):
        return self.document.get_content()

    def get_storage_text(self):
        return self.document.get_storage_content()

    def get_legacy_text(self):
        return self.document.get_legacy_content()

    def get_text_position_map(self):
        return self.document.get_text_position_map()

    def get_legacy_text_position_map(self):
        return self.document.get_legacy_text_position_map()

    def iter_content_hash_images(self):
        return self.document.iter_content_hash_images()

    def display_to_storage_position(self, pos, affinity="before"):
        return self.document.display_to_storage_position(pos, affinity=affinity)

    def storage_to_display_position(self, pos, affinity="before"):
        return self.document.storage_to_display_position(pos, affinity=affinity)

    def display_to_storage_range(self, start, stop):
        return self.document.display_to_storage_range(start, stop)

    def storage_to_display_range(self, start, stop):
        return self.document.storage_to_display_range(start, stop)

    def legacy_to_storage_position(self, pos, affinity="before"):
        return self.document.legacy_to_storage_position(pos, affinity=affinity)

    def legacy_to_storage_range(self, start, stop):
        return self.document.legacy_to_storage_range(start, stop)

    def get_semantic_structure(self):
        return self.document.get_document_semantic_structure()

    def get_table_markup(self, table_index):
        return self.document.get_document_table_markup(table_index)

    def get_embedded_image(self, image_index: int) -> ImageIO:
        return self.document.get_document_embedded_image(image_index)

    def get_embedded_image_info(self, image_index: int):
        return self.document.get_document_embedded_image_info(image_index)

    def get_style_info(self):
        return self.document.get_document_style_info()

    def resolve_link(self, link_range):
        return self.document.resolve_link(link_range)


class SinglePageDocument(BaseDocument):
    """Provides sain defaults for single page documents."""

    def __len__(self):
        return 1

    @abstractmethod
    def get_content(self) -> str:
        """Get the content of this document."""

    def get_storage_content(self) -> str:
        return self.get_content()

    def get_legacy_content(self) -> str:
        return self.get_content()

    def get_text_position_map(self) -> TextPositionMap:
        return TextPositionMap.identity(len(self.get_content()))

    def get_legacy_text_position_map(self) -> TextPositionMap:
        if hasattr(self, "_legacy_text_position_map"):
            return self._legacy_text_position_map
        self._legacy_text_position_map = TextPositionMap.from_texts(
            self.get_legacy_content(),
            self.get_storage_content(),
        )
        return self._legacy_text_position_map

    def display_to_storage_position(self, pos: int, affinity="before") -> int:
        return self.get_text_position_map().display_to_storage_position(pos, affinity=affinity)

    def storage_to_display_position(self, pos: int, affinity="before") -> int:
        return self.get_text_position_map().storage_to_display_position(pos, affinity=affinity)

    def display_to_storage_range(self, start: int, stop: int) -> TextRange:
        return self.get_text_position_map().display_to_storage_range(start, stop)

    def storage_to_display_range(self, start: int, stop: int) -> TextRange:
        return self.get_text_position_map().storage_to_display_range(start, stop)

    def legacy_to_storage_position(self, pos: int, affinity="before") -> int:
        return self.get_legacy_text_position_map().display_to_storage_position(
            pos,
            affinity=affinity,
        )

    def legacy_to_storage_range(self, start: int, stop: int) -> TextRange:
        return self.get_legacy_text_position_map().display_to_storage_range(start, stop)

    def get_legacy_content_hash(self) -> str | None:
        if self._cache_legacy_content_hash_if_possible():
            return self._legacy_content_hash
        if not self._is_read:
            self.read()
        self._legacy_content_hash = self._hash_document_text(self.get_legacy_content())
        return self._legacy_content_hash

    def get_page(self, index: int) -> SinglePage:
        return SinglePage(self, index)

    @cached_property
    def language(self) -> str:
        return self.get_language(samples=self.get_content()[:2000], is_html=False)

    def get_section_at_position(self, pos):
        """Return the section at the given position."""
        rv = self.toc_tree
        for sect in rv.iter_children():
            if pos in sect.text_range:
                rv = sect
                if sect.text_range.start > pos:
                    break
        return rv

    def get_document_semantic_structure(self):
        raise NotImplementedError

    def get_document_style_info(self):
        raise NotImplementedError

    def get_document_table_markup(self, table_index):
        raise NotImplementedError

    def get_document_embedded_image(self, image_index: int) -> ImageIO:
        raise NotImplementedError

    def get_document_embedded_image_info(self, image_index: int):
        raise NotImplementedError

    def resolve_link(self, text_range):
        raise NotImplementedError

    def search(self, request: doctools.SearchRequest):
        text = self.get_content()[request.text_range.as_slice()]
        yield from QueueProcess(
            target=doctools.search_single_page_document,
            args=(
                text,
                request,
            ),
            name="document-search",
        )


class DummyDocument(BaseDocument):
    """Implements core document methods for a dummy document."""

    __indexable__ = True

    def __len__(self):
        raise NotImplementedError

    def get_page(self, index):
        raise NotImplementedError

    @property
    def toc_tree(self):
        raise NotImplementedError

    @property
    def metadata(self):
        raise NotImplementedError


class VirtualDocument:
    """
    A Marker to denote a virtual document.
    Subclasses of this should be considered one shot documents.
    """

    def __init__(self):
        self.uri.view_args.update(
            {
                "is_virtual": True,
                "save_last_position": False,
                "add_to_recents": False,
                "allow_pinning": False,
            }
        )

    def search(self, request: doctools.SearchRequest):
        yield from doctools.search_book(self, request)

    def export_to_text(self, target_filename: t.PathLike):
        yield from doctools.export_to_plain_text(self, target_filename)
