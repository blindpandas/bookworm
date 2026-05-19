
from __future__ import annotations

import re
from functools import cached_property
from itertools import chain
from pathlib import PurePosixPath
from urllib import parse as urllib_parse

import ftfy
from inscriptis import Inscriptis
from inscriptis.css_profiles import STRICT_CSS_PROFILE
from inscriptis.model.config import ParserConfig
from lxml import html as html_parser
from selectolax.parser import HTMLParser

from bookworm.logger import logger
from bookworm.structured_text import (
    ImageElementInfo,
    SemanticElementType,
    TextPositionMap,
    TextRange,
)
from bookworm.utils import remove_excess_blank_lines

log = logger.getChild(__name__)
IMAGE_ANNOTATION = "__bookworm_image__"
INSCRIPTIS_PARSE_HTML_TREE = Inscriptis._parse_html_tree
INSCRIPTIS_GET_TEXT = Inscriptis.get_text
MAX_DECODE_LENGTH = int(5e6)
RE_STRIP_XML_DECLARATION = re.compile(r"^<\?xml [^>]+?\?>")
TAGS_TO_STRIP = [
    "form",
    "input",
    "button",
    "select",
    "fieldset",
    "legend",
    "strong",
    "small",
    "link",
    "span",
    "emph",
    "b",
    "i",
    "img",
    "sub",
    "sup",
]
SEMANTIC_HTML_ELEMENTS = {
    SemanticElementType.HEADING_1: {
        "h1",
        "#aria-role=heading",
    },
    SemanticElementType.HEADING_2: {
        "h2",
    },
    SemanticElementType.HEADING_3: {
        "h3",
    },
    SemanticElementType.HEADING_4: {
        "h4",
    },
    SemanticElementType.HEADING_5: {
        "h5",
    },
    SemanticElementType.HEADING_6: {
        "h6",
    },
    SemanticElementType.LINK: {
        "a#href",
        "a#name",
    },
    SemanticElementType.LIST: {
        "ol",
        "ul",
    },
    SemanticElementType.QUOTE: {
        "blockquote",
        "q",
    },
    SemanticElementType.TABLE: {
        "table",
    },
    # SemanticElementType.FIGURE: {
    # "img",
    # "figure",
    # "picture",
    # }
}
STYLE_HTML_ELEMENTS = {}
INSCRIPTIS_ANNOTATION_RULES = {t: (k,) for (k, v) in SEMANTIC_HTML_ELEMENTS.items() for t in v}
INSCRIPTIS_ANNOTATION_RULES["img#src"] = (IMAGE_ANNOTATION,)
INSCRIPTIS_CONFIG = ParserConfig(
    css=STRICT_CSS_PROFILE,
    display_images=False,
    deduplicate_captions=True,
    display_links=False,
    annotation_rules=INSCRIPTIS_ANNOTATION_RULES,
)


class StructuredHtmlParser(Inscriptis):
    """Subclass of ```inscriptis.Inscriptis``` to provide the position of structural elements."""

    __slots__ = [
        "_display_text",
        "_image_elements",
        "_storage_text",
        "_table_elements",
        "_text_position_map",
        "anchors",
        "link_range_to_target",
        "styled_elements",
    ]

    @staticmethod
    def normalize_html(html_string):
        config = ftfy.TextFixerConfig(
            fix_character_width=False,
            uncurl_quotes=False,
            fix_latin_ligatures=False,
            normalization="NFC",
            unescape_html=False,
            fix_line_breaks=True,
            max_decode_length=MAX_DECODE_LENGTH,
        )
        html_string = ftfy.fix_text(html_string, config)
        return remove_excess_blank_lines(html_string)

    def __init__(self, *args, include_images=True, **kwargs):
        self.link_range_to_target = {}
        self.anchors = {}
        self.html_id_ranges = {}
        self.styled_elements = {}
        self._table_elements = []
        self._image_elements = []
        self._display_text = ""
        self._storage_text = ""
        self._text_position_map = TextPositionMap.identity(0)
        kwargs.setdefault("config", INSCRIPTIS_CONFIG)
        if include_images and args:
            self._prepare_image_elements(args[0])
        super().__init__(*args, **kwargs)
        self._display_text = remove_excess_blank_lines(INSCRIPTIS_GET_TEXT(self))
        self._storage_text, self._text_position_map = TextPositionMap.from_collapsed_ranges(
            self._display_text,
            (image.text_range for image in self._get_visible_image_elements()),
        )

    def _parse_html_tree(self, state, tree):
        canvas = state.canvas
        start_index = self._get_canvas_index(canvas)
        super()._parse_html_tree(state, tree)
        end_index = self._get_canvas_index(canvas)
        try:
            anot = canvas.annotations[-1]
        except IndexError:
            pass
        else:
            if tree.tag == "a" and (href := tree.attrib.get("href", "")):
                self.link_range_to_target[(anot.start, anot.end)] = href
        if (anch := tree.attrib.get("id", "")) or (anch := tree.attrib.get("name", "")):
            element_range = (start_index, end_index)
            self.anchors[anch] = element_range
            self.html_id_ranges[anch] = element_range
        if tree.tag == "table":
            self._table_elements.append(tree)
            self._resolve_table_image_ranges(
                tree,
                canvas.get_text(),
                canvas.annotations,
                start_index,
                end_index,
            )
        if (
            tree.tag == "img"
            and (src := tree.attrib.get("src", ""))
            and self._is_navigable_image(tree)
        ):
            label = self._get_image_label(tree)
            placeholder = self._get_image_placeholder(label)
            text_range = self._find_placeholder_range(
                canvas.get_text(),
                placeholder,
                start_index,
                end_index,
            )
            self._image_elements.append(
                ImageElementInfo(
                    text_range=text_range or TextRange(-1, -1),
                    src=src,
                    label=label,
                    suggested_filename=self._get_suggested_filename(src),
                )
            )

        return state.canvas

    @staticmethod
    def _get_canvas_index(canvas):
        try:
            return canvas.current_block.idx
        except TypeError:
            return 0

    @classmethod
    def _prepare_image_elements(cls, tree):
        for image in tree.iter("img"):
            if not cls._is_navigable_image(image):
                continue
            label = cls._get_image_label(image)
            placeholder = cls._get_image_placeholder(label)
            image.text = placeholder if image.text is None else f"{placeholder} {image.text}"

    @classmethod
    def _is_navigable_image(cls, image):
        return (
            bool(image.attrib.get("src", ""))
            and not cls._is_hidden_image(image)
            and not cls._is_decorative_image(image)
        )

    @classmethod
    def _is_decorative_image(cls, image):
        return cls._has_empty_alt(image) and not cls._get_non_alt_image_label(image)

    @staticmethod
    def _has_empty_alt(image):
        return "alt" in image.attrib and not image.attrib.get("alt", "").strip()

    @classmethod
    def _get_non_alt_image_label(cls, image):
        for label in (
            image.attrib.get("title", ""),
            cls._get_figure_caption(image),
        ):
            label = cls._normalize_image_label(label)
            if label:
                return label
        return ""

    @staticmethod
    def _is_hidden_image(image):
        return any(
            StructuredHtmlParser._is_hidden_element(element)
            for element in chain((image,), image.iterancestors())
        )

    @staticmethod
    def _is_hidden_element(element):
        return "hidden" in element.attrib or StructuredHtmlParser._has_display_none(element)

    @staticmethod
    def _has_display_none(element):
        for directive in element.attrib.get("style", "").lower().split(";"):
            if ":" not in directive:
                continue
            key, value = (part.strip() for part in directive.split(":", 1))
            value = value.split("!", 1)[0].strip()
            if key == "display" and value == "none":
                return True
        return False

    @staticmethod
    def _get_image_placeholder(label):
        return f"[{label}]"

    @classmethod
    def _find_placeholder_range(cls, text, placeholder, start=0, stop=None):
        if stop is None or stop < start:
            stop = len(text)
        start = max(start, 0)
        index = text.find(placeholder, start, stop)
        if index == -1:
            return None
        return TextRange(index, index + len(placeholder))

    def _resolve_table_image_ranges(
        self,
        table,
        text,
        annotations,
        start_index,
        end_index,
    ):
        table_image_infos = self._get_table_image_infos(table)
        if not table_image_infos:
            return
        image_annotations = self._get_image_annotations(
            annotations,
            start_index,
            end_index,
        )
        for image_info, annotation in zip(table_image_infos, image_annotations):
            text_range = self._get_placeholder_range_from_annotation(
                text,
                annotation,
                image_info.label,
            )
            if not text_range:
                continue
            image_info.text_range.start = text_range.start
            image_info.text_range.stop = text_range.stop

    def _get_table_image_infos(self, table):
        table_image_count = sum(1 for image in table.iter("img") if self._is_navigable_image(image))
        if not table_image_count:
            return ()
        return self._image_elements[-table_image_count:]

    @staticmethod
    def _get_image_annotations(annotations, start_index, end_index):
        return tuple(
            annotation
            for annotation in annotations
            if annotation.metadata == IMAGE_ANNOTATION
            and start_index <= annotation.start
            and annotation.end <= end_index
        )

    def _get_placeholder_range_from_annotation(self, text, annotation, label):
        placeholder = self._get_image_placeholder(label)
        return self._find_placeholder_range(
            text,
            placeholder,
            annotation.start,
            annotation.end,
        ) or TextRange(annotation.start, annotation.end)

    def _get_visible_image_elements(self):
        return tuple(
            image_info for image_info in self._image_elements if image_info.text_range.start >= 0
        )

    def iter_image_storage_ranges(self):
        for image_info in self._get_visible_image_elements():
            yield image_info, self.display_to_storage_range(
                image_info.text_range.start,
                image_info.text_range.stop,
            )

    @staticmethod
    def _get_image_label(image):
        for label in (
            image.attrib.get("alt", ""),
            image.attrib.get("title", ""),
            StructuredHtmlParser._get_figure_caption(image),
        ):
            label = StructuredHtmlParser._normalize_image_label(label)
            if label:
                return label
        return _("Image")

    @staticmethod
    def _get_figure_caption(image):
        for figure in image.iterancestors("figure"):
            caption = " ".join(figure.xpath(".//figcaption//text()")).strip()
            if caption:
                return caption
        return ""

    @staticmethod
    def _normalize_image_label(label):
        label = " ".join(label.split())
        if not label or not any(char.isalnum() for char in label):
            return ""
        return label

    @staticmethod
    def _get_suggested_filename(src):
        if src.lower().startswith("data:image/"):
            media_type = src.split(",", 1)[0].split(";", 1)[0]
            image_type = media_type.split("/", 1)[-1].split("+", 1)[0]
            if image_type == "jpeg":
                image_type = "jpg"
            return f"image.{image_type or 'png'}"
        path = urllib_parse.urlparse(src).path
        filename = PurePosixPath(urllib_parse.unquote(path)).name
        return filename or _("Image")

    @classmethod
    def preprocess_html_string(cls, html_string):
        html_content = html_string.strip()
        if not html_content:
            raise ValueError("Invalid html content")
        # strip XML declaration, if necessary
        if html_content.startswith("<?xml "):
            html_content = RE_STRIP_XML_DECLARATION.sub("", html_content, count=1)
        html_content = cls.normalize_html(html_content)
        return html_content

    @classmethod
    def from_string(cls, html_string, *, include_images=True):
        html_content = cls.preprocess_html_string(html_string)
        return cls(
            html_parser.fromstring(html_content),
            include_images=include_images,
        )

    @classmethod
    def from_lxml_html_tree(cls, lxml_html_tree, *, include_images=True):
        return cls(lxml_html_tree, include_images=include_images)

    def get_text(self):
        return self._display_text

    def get_storage_text(self):
        return self._storage_text

    @property
    def text_position_map(self):
        return self._text_position_map

    def display_to_storage_position(self, pos, affinity="before"):
        return self._text_position_map.display_to_storage_position(pos, affinity=affinity)

    def storage_to_display_position(self, pos, affinity="before"):
        return self._text_position_map.storage_to_display_position(pos, affinity=affinity)

    def display_to_storage_range(self, start, stop):
        return self._text_position_map.display_to_storage_range(start, stop)

    def storage_to_display_range(self, start, stop):
        return self._text_position_map.storage_to_display_range(start, stop)

    @cached_property
    def semantic_elements(self):
        annotations = {}
        for anot in self.get_annotations():
            if anot.metadata == IMAGE_ANNOTATION:
                continue
            annotations.setdefault(anot.metadata, []).append((anot.start, anot.end))
        if self._image_elements:
            image_ranges = annotations.setdefault(SemanticElementType.FIGURE, [])
            image_ranges.extend(
                image.text_range.astuple() for image in self._get_visible_image_elements()
            )
        return annotations

    @cached_property
    def link_targets(self):
        return self.link_range_to_target

    def get_table_markup(self, table_index):
        parsed = HTMLParser(
            html_parser.tostring(self._table_elements[table_index], encoding="unicode")
        )
        parsed.unwrap_tags(
            [
                "a",
            ]
        )
        return parsed.html

    def get_image_info(self, image_index):
        return self._get_visible_image_elements()[image_index]
