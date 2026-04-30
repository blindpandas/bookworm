# coding: utf-8

import functools
import os
import threading
import time
from copy import copy
from enum import IntEnum
from functools import cached_property
from pathlib import Path

import wx
from PIL import Image

from bookworm import app, config, speech
from bookworm.concurrency import QueueProcess, call_threaded, threaded_worker
from bookworm.document import SINGLE_PAGE_DOCUMENT_PAGER, BookMetadata
from bookworm.document import DocumentCapability as DC
from bookworm.document import DocumentUri, Section, SinglePageDocument, VirtualDocument
from bookworm.gui.components import AsyncSnakDialog, RobustProgressDialog, SimpleDialog
from bookworm.gui.settings import ReconciliationStrategies, SettingsPanel
from bookworm.i18n import LocaleInfo
from bookworm.image_io import ImageIO
from bookworm.logger import logger
from bookworm.ocr_engines import OcrRequest
from bookworm.ocr_engines.base import (
    OcrError,
    OcrAuthenticationError,
    OcrNetworkError,
    OcrProcessingError,
    OcrResult,
)
from bookworm.resources import sounds
from bookworm.signals import (
    _signals,
    reader_book_loaded,
    reader_book_unloaded,
    reader_page_changed,
)
from bookworm.utils import gui_thread_safe

from .ocr_dialogs import OCROptionsDialog

try:
    from bookworm.text_to_speech import should_auto_navigate_to_next_page
except ImportError:
    should_auto_navigate_to_next_page = None


log = logger.getChild(__name__)

# Signals
ocr_started = _signals.signal("ocr-started")
ocr_ended = _signals.signal("ocr-ended")


class _ImageOcrRegonitionResultsDocument(VirtualDocument, SinglePageDocument):
    __internal__ = True
    format = "ocr_image_recog"
    name = "Image Recognition Results"
    extensions = ()
    capabilities = DC.SINGLE_PAGE | DC.LINKS | DC.STRUCTURED_NAVIGATION

    def __init__(self, *args, ocr_result, image_name, **kwargs):
        super(SinglePageDocument, self).__init__(*args, **kwargs)
        VirtualDocument.__init__(self)
        self.ocr_result = ocr_result
        self.language = ocr_result.ocr_request.language
        self.image_name = image_name

    def read(self):
        super().read()

    def get_content(self):
        return self.ocr_result.recognized_text

    @cached_property
    def language(self):
        return self.language

    def close(self):
        super().close()

    @cached_property
    def toc_tree(self):
        return Section(
            title="",
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
        )

    @cached_property
    def metadata(self):
        return BookMetadata(
            title=_("Recognition Result: {image_name}").format(
                image_name=self.image_name
            ),
            author="",
            publication_year="",
        )


class _MarkdownOcrRecognitionResultsDocument(VirtualDocument, SinglePageDocument):
    """OCR result document with Markdown semantic parsing for structured navigation."""

    __internal__ = True
    format = "ocr_markdown_recog"
    name = "Markdown OCR Recognition Results"
    extensions = ()
    capabilities = (
        DC.TOC_TREE
        | DC.SINGLE_PAGE
        | DC.STRUCTURED_NAVIGATION
        | DC.TEXT_STYLE
        | DC.LINKS
        | DC.INTERNAL_ANCHORS
    )

    def __init__(self, *args, ocr_result, image_name, **kwargs):
        super(SinglePageDocument, self).__init__(*args, **kwargs)
        VirtualDocument.__init__(self)
        self.ocr_result = ocr_result
        self._language = ocr_result.ocr_request.language
        self.image_name = image_name
        self._text = None
        self._semantic_structure = {}
        self._style_info = {}
        self._outline = None
        self.link_targets = {}
        self.anchors = {}
        self.structure = None

    def read(self):
        super().read()
        self._parse_markdown_content()

    def _parse_markdown_content(self):
        from mistune import markdown as mistune_markdown
        from bookworm.structured_text import HEADING_LEVELS, TextRange
        from bookworm.structured_text.structured_html_parser import StructuredHtmlParser
        from bookworm.document import TreeStackBuilder
        from more_itertools import zip_offset

        md_content = self.ocr_result.recognized_text
        rendered_html = mistune_markdown(md_content, escape=False)
        html_string = "\n".join([
            "<!doctype html>",
            "<html>",
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{self.image_name}</title>",
            "</head>",
            "<body>",
            rendered_html,
            "</body>",
            "</html>",
        ])

        extracted = StructuredHtmlParser.from_string(html_string)
        self.structure = extracted
        self._semantic_structure = extracted.semantic_elements
        self._style_info = extracted.styled_elements
        self.link_targets = extracted.link_targets
        self.anchors = extracted.anchors
        self._text = text = extracted.get_text()

        heading_poses = sorted(
            (
                (rng, h)
                for h, rngs in extracted.semantic_elements.items()
                for rng in rngs
                if h in HEADING_LEVELS
            ),
            key=lambda x: x[0],
        )

        root = Section(
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
            text_range=TextRange(0, -1),
            title=self.image_name,
            level=1,
        )
        stack = TreeStackBuilder(root)
        for (start_pos, stop_pos), h_element in heading_poses:
            h_text = text[start_pos:stop_pos].strip()
            h_level = int(h_element.name[-1])
            section = Section(
                pager=SINGLE_PAGE_DOCUMENT_PAGER,
                title=h_text,
                level=h_level,
                text_range=TextRange(start_pos, stop_pos),
            )
            stack.push(section)
        all_sections = tuple(root.iter_children())
        for this_sect, next_sect in zip_offset(
            all_sections, all_sections, offsets=(0, 1)
        ):
            this_sect.text_range.stop = next_sect.text_range.start - 1
        last_pos = len(text)
        if all_sections:
            all_sections[-1].text_range.stop = last_pos
        root.text_range = TextRange(0, last_pos)
        self._outline = root

    def get_content(self):
        return self._text

    def get_document_semantic_structure(self):
        return self._semantic_structure

    def get_document_style_info(self):
        return self._style_info

    def get_document_table_markup(self, table_index):
        if self.structure is not None:
            return self.structure.get_table_markup(table_index)

    def resolve_link(self, link_range):
        from bookworm.document import LinkTarget
        from bookworm.utils import is_external_url

        href = self.link_targets.get(link_range)
        if href is None:
            return None
        if is_external_url(href):
            return LinkTarget(url=href, is_external=True)
        else:
            _filename, anchor = href.split("#") if "#" in href else (href, None)
            if anchor := self.anchors.get(anchor, None):
                return LinkTarget(url=href, is_external=False, position=anchor)

    @cached_property
    def language(self):
        return self._language

    def close(self):
        super().close()

    @cached_property
    def toc_tree(self):
        if self._outline is not None:
            root = self._outline
            if len(root) == 1:
                return root[0]
            return root
        return Section(
            title=self.image_name,
            pager=SINGLE_PAGE_DOCUMENT_PAGER,
        )

    @cached_property
    def metadata(self):
        return BookMetadata(
            title=_("Recognition Result: {image_name}").format(
                image_name=self.image_name
            ),
            author="",
            publication_year="",
        )


class OCRMenuIds(IntEnum):
    scanCurrentPage = 10001
    autoScanPages = 10002
    scanToTextFile = 10003
    changeOCROptions = 10004


OCR_KEYBOARD_SHORTCUTS = {
    OCRMenuIds.scanCurrentPage: "F4",
    OCRMenuIds.autoScanPages: "Ctrl-F4",
}


class OCRMenu(wx.Menu):
    """OCR menu."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.view = service.view
        self._ocr_cancelled = threading.Event()
        image2textId = wx.NewIdRef()

        # Add menu items
        self.Append(
            OCRMenuIds.scanCurrentPage,
            # Translators: the label of an item in the application menubar
            _("&Scan Current Page...\tF4"),
            # Translators: the help text of an item in the application menubar
            _("Run OCR on the current page"),
        )
        self.auto_scan_item = self.Append(
            OCRMenuIds.autoScanPages,
            # Translators: the label of an item in the application menubar
            _("&Automatic OCR\tCtrl-F4"),
            # Translators: the help text of an item in the application menubar
            _("Auto run  OCR when turning pages."),
            kind=wx.ITEM_CHECK,
        )
        self.Append(
            OCRMenuIds.changeOCROptions,
            # Translators: the label of an item in the application menubar
            _("&Change OCR Options..."),
            # Translators: the help text of an item in the application menubar
            _("Change OCR options"),
        )
        self.Append(
            OCRMenuIds.scanToTextFile,
            # Translators: the label of an item in the application menubar
            _("Scan To &Text File..."),
            # Translators: the help text of an item in the application menubar
            _("Scan pages and save the text to a .txt file."),
        )
        self.Append(
            image2textId,
            # Translators: the label of an item in the application menubar
            _("Image To Text..."),
            # Translators: the help text of an item in the application menubar
            _("Run OCR on an image."),
        )
        # Add the menu to the menubar
        # Translators: the label of the OCR menu in the application menubar
        # Event handlers
        self.view.Bind(
            wx.EVT_MENU, self.onScanCurrentPage, id=OCRMenuIds.scanCurrentPage
        )
        self.view.Bind(wx.EVT_MENU, self.onAutoScanPages, id=OCRMenuIds.autoScanPages)
        self.view.Bind(wx.EVT_MENU, self.onScanToTextFile, id=OCRMenuIds.scanToTextFile)
        self.view.Bind(
            wx.EVT_MENU, self.onChangeOCROptions, id=OCRMenuIds.changeOCROptions
        )
        self.view.Bind(wx.EVT_MENU, self.onScanImageFile, id=image2textId)
        self.view.add_load_handler(self._on_reader_loaded)
        reader_book_unloaded.connect(self._on_reader_unloaded, sender=self.view.reader)
        reader_page_changed.connect(
            self._on_reader_page_changed, sender=self.service.reader
        )
        if should_auto_navigate_to_next_page:
            should_auto_navigate_to_next_page.connect(
                self.on_should_auto_navigate_to_next_page, sender=self.view
            )
        self._saved_pdf_uri = None
        self._saved_pdf_page = None
        self.view.contentTextCtrl.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _get_ocr_options(self, from_cache=True, **dlg_kw):
        last_stored_opts = self.service.stored_options
        if not from_cache:
            self.service.stored_options = None
            self.service.saved_scanned_pages.clear()
        if self.service.stored_options is not None:
            return self.service.stored_options
        else:
            opts = self._get_ocr_options_from_dlg(
                last_stored_options=last_stored_opts, **dlg_kw
            )
            if opts is not None and opts.store_options:
                self.service.stored_options = opts
            else:
                self.service.stored_options = None
            return opts

    def _get_ocr_options_from_dlg(self, last_stored_options=None, **dlg_kw):
        self.service._init_ocr_engine()
        engine = self.service.current_ocr_engine
        langs = engine.get_sorted_languages()
        if not langs:
            wx.MessageBox(
                # Translators: content of a message
                _(
                    "No language for OCR is present.\nPlease checkout Bookworm user manual to learn how to add new languages."
                ),
                # Translators: title for a message
                _("No Languages for OCR"),
                style=wx.ICON_ERROR,
            )
            return
        dlg = OCROptionsDialog(
            parent=self.view,
            title=_("OCR Options"),
            engine=engine,
            languages=langs,
            stored_options=last_stored_options,
            is_multilingual=engine.__supports_more_than_one_recognition_language__,
            **dlg_kw,
        )
        self.service.saved_scanned_pages.clear()
        return dlg.ShowModal()

    @staticmethod
    def _parse_markdown_for_display(md_content):
        """Convert Markdown to plain text and extract semantic structure."""
        from mistune import markdown as mistune_markdown
        from bookworm.structured_text.structured_html_parser import StructuredHtmlParser

        html = mistune_markdown(md_content, escape=False)
        html_string = (
            "<!doctype html><html><head>"
            '<meta charset="utf-8"></head><body>'
            f"{html}</body></html>"
        )
        extracted = StructuredHtmlParser.from_string(html_string)
        return extracted.get_text(), extracted.semantic_elements

    @staticmethod
    def _markdown_to_plain_text(md_content):
        """Convert Markdown to clean plain text with readable table layout."""
        text, _ = OCRMenu._parse_markdown_for_display(md_content)
        return text

    def _display_ocr_markdown(self, page_number, md_content):
        """Parse Markdown, display plain text, and inject semantic structure."""
        text, semantic = self._parse_markdown_for_display(md_content)
        self.service.saved_scanned_pages[page_number] = (text, semantic)
        if page_number == self.service.reader.current_page:
            self._set_content_with_semantics(text, semantic)

    def _set_content_with_semantics(self, text, semantic):
        self.view.set_content(text)
        page = self.service.reader.document.get_page(
            self.service.reader.current_page
        )
        page._injected_semantic_structure = semantic

    @staticmethod
    def _try_fitz_extract_markdown(document, page_number):
        """Try to extract structured Markdown directly from PDF text layer.
        Returns Markdown string if the page has a text layer, None otherwise.
        """
        try:
            import fitz  # noqa: PLC0415
        except ImportError:
            return None
        fitz_doc = getattr(document, "_ebook", None)
        if fitz_doc is None or not isinstance(fitz_doc, fitz.Document):
            return None
        page = fitz_doc[page_number]
        plain = page.get_text("text").strip()
        if len(plain) < 20:
            return None
        parts = []
        tables = page.find_tables()
        table_rects = [t.bbox for t in tables.tables] if tables.tables else []
        if table_rects:
            blocks = page.get_text("dict", sort=True)["blocks"]
            for block in blocks:
                if block["type"] != 0:
                    continue
                bx0, by0, bx1, by1 = block["bbox"]
                in_table = any(
                    bx0 >= tr[0] - 5 and by0 >= tr[1] - 5
                    and bx1 <= tr[2] + 5 and by1 <= tr[3] + 5
                    for tr in table_rects
                )
                if not in_table:
                    for line in block["lines"]:
                        text = "".join(
                            span["text"] for span in line["spans"]
                        ).strip()
                        if text:
                            max_size = max(
                                (s["size"] for s in line["spans"]), default=0
                            )
                            is_bold = any(
                                "bold" in s["font"].lower()
                                for s in line["spans"]
                            )
                            if max_size > 16 and is_bold:
                                parts.append(f"## {text}")
                            elif max_size > 14 and is_bold:
                                parts.append(f"### {text}")
                            else:
                                parts.append(text)
            for table in tables.tables:
                md_table = table.to_markdown()
                parts.append(md_table)
        else:
            blocks = page.get_text("dict", sort=True)["blocks"]
            for block in blocks:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    text = "".join(
                        span["text"] for span in line["spans"]
                    ).strip()
                    if text:
                        max_size = max(
                            (s["size"] for s in line["spans"]), default=0
                        )
                        is_bold = any(
                            "bold" in s["font"].lower()
                            for s in line["spans"]
                        )
                        if max_size > 16 and is_bold:
                            parts.append(f"## {text}")
                        elif max_size > 14 and is_bold:
                            parts.append(f"### {text}")
                        else:
                            parts.append(text)
        return "\n\n".join(parts) if parts else None

    def onScanCurrentPage(self, event):
        self._ocr_cancelled.clear()
        ocr_opts = self._get_ocr_options()
        if ocr_opts is None:
            return speech.announce(_("Canceled"), True)
        reader = self.service.reader
        if reader.current_page in self.service.saved_scanned_pages:
            cached = self.service.saved_scanned_pages[reader.current_page]
            if isinstance(cached, tuple):
                self._set_content_with_semantics(cached[0], cached[1])
            else:
                self.view.set_content(cached)
            return

        # Fast path: try direct text extraction from PDF text layer
        if self._is_glm_markdown_mode():
            md_content = self._try_fitz_extract_markdown(
                reader.document, reader.current_page
            )
            if md_content:
                log.info(
                    "Fast path: extracted text layer from page %d",
                    reader.current_page,
                )
                self._display_ocr_markdown(reader.current_page, md_content)
                sounds.ocr_end.play()
                return

        # Medium path: GLM-OCR Cloud — send single-page PDF directly
        if self._is_glm_markdown_mode() and self._can_use_cloud_pdf_direct(reader):
            self._cloud_pdf_single_page(reader.current_page)
            return

        # Slow path: screenshot-based OCR (Ollama / other engines)
        image = reader.document.get_page_image(
            reader.current_page,
            ocr_opts.zoom_factor,
        )
        ocr_request = OcrRequest(
            languages=ocr_opts.languages,
            image=image,
            image_processing_pipelines=ocr_opts.image_processing_pipelines,
            cookie=reader.current_page,
            engine_options=ocr_opts.engine_options,
        )

        def _ocr_callback(ocr_result):
            page_number = ocr_result.cookie
            content = ocr_result.recognized_text
            if self._is_glm_markdown_mode():
                self._display_ocr_markdown(page_number, content)
            else:
                self.service.saved_scanned_pages[page_number] = content
                if page_number == self.view.reader.current_page:
                    self.view.set_content(content)
                    self.view.set_text_direction(ocr_request.language.is_rtl)

        self._run_ocr(ocr_request, _ocr_callback)

    def _open_ocr_virtual_document(self, recog_document):
        """Open an OCR virtual document, saving the current PDF state for Escape return."""
        current_reader = self.service.reader
        if not getattr(self, "_saved_pdf_uri", None):
            self._saved_pdf_uri = current_reader.document.uri
            self._saved_pdf_page = current_reader.current_page
        wx.CallAfter(self._load_and_focus, recog_document)

    def _load_and_focus(self, recog_document):
        self.view.load_document(recog_document)
        self.view.contentTextCtrl.SetFocus()

    def _return_to_pdf(self):
        """Return to the original PDF after viewing an OCR virtual document."""
        saved_uri = getattr(self, "_saved_pdf_uri", None)
        if saved_uri is None:
            return False
        saved_page = getattr(self, "_saved_pdf_page", 0)
        self._saved_pdf_uri = None
        self._saved_pdf_page = None
        uri_with_page = saved_uri.create_copy(
            openner_args={"page": str(saved_page)}
        )
        wx.CallAfter(self._open_uri_and_focus, uri_with_page)
        return True

    def _open_uri_and_focus(self, uri):
        self.view.open_uri(uri)
        wx.CallLater(200, self.view.contentTextCtrl.SetFocus)

    def _on_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE and self._saved_pdf_uri is not None:
            self._return_to_pdf()
            return
        event.Skip()

    def _can_use_cloud_pdf_direct(self, reader):
        """Check if we can use direct PDF upload for the current document."""
        engine = self.service.current_ocr_engine
        if not (hasattr(engine, "_get_mode") and engine._get_mode().value == "cloud"):
            return False
        doc = reader.document
        if not hasattr(doc, "get_file_system_path"):
            return False
        try:
            pdf_path = doc.get_file_system_path()
            return pdf_path and Path(pdf_path).suffix.lower() == ".pdf"
        except Exception:
            return False

    def _cloud_pdf_single_page(self, page_number):
        """OCR a single page via Cloud: extract page as temp PDF and upload."""
        sounds.ocr_start.play()
        ocr_started.send(sender=self.view)
        reader = self.service.reader
        pdf_path = reader.document.get_file_system_path()

        def _task():
            from bookworm.ocr_engines.glm_ocr import GlmOcrEngine  # noqa: PLC0415
            return GlmOcrEngine.recognize_single_page_pdf(pdf_path, page_number)

        def _done(future):
            try:
                md_content = future.result()
            except Exception:
                log.exception("Cloud PDF direct OCR failed for page %d.", page_number)
                ocr_ended.send(sender=self.view, isfaulted=True)
                wx.CallAfter(
                    wx.MessageBox,
                    _("Cloud PDF OCR failed. Falling back may be needed."),
                    _("OCR Error"),
                    style=wx.ICON_ERROR,
                    parent=self.view,
                )
                return

            self._display_ocr_markdown(page_number, md_content)
            sounds.ocr_end.play()
            ocr_ended.send(sender=self.view, isfaulted=False)

        self._wait_dlg = AsyncSnakDialog(
            task=_task,
            done_callback=_done,
            message=_("Running OCR, please wait..."),
            dismiss_callback=self._on_ocr_cancelled,
            parent=self.view,
        )

    def _run_ocr(self, ocr_request, callback):
        ocr_started.send(sender=self.view)
        # Show a modal dialog
        sounds.ocr_start.play()
        future_callback = functools.partial(self._process_ocr_result, callback)
        self._wait_dlg = AsyncSnakDialog(
            task=functools.partial(
                self.service.current_ocr_engine.preprocess_and_recognize, ocr_request
            ),
            done_callback=future_callback,
            message=_("Running OCR, please wait..."),
            dismiss_callback=self._on_ocr_cancelled,
            parent=self.view,
        )

    def onAutoScanPages(self, event):
        event.Skip()
        # We only need to ask for options if the user is TURNING ON auto-scan
        # and no options have been stored yet.
        if self.auto_scan_item.IsChecked() and self.service.stored_options is None:
            # force_save=True ensures the "store options" checkbox is hidden and on by default
            opts = self._get_ocr_options(from_cache=False, force_save=True)
            if opts is None:
                # User clicked Cancel while setting up auto-scan options.
                speech.announce(_("Automatic OCR setup canceled."), True)
                self.auto_scan_item.Check(False)
                return
        # Announce the final state of the checkbox
        if self.auto_scan_item.IsChecked():
            speech.announce(_("Automatic OCR is enabled"))
            if self.view.is_empty():
                self.onScanCurrentPage(event)
        else:
            speech.announce(_("Automatic OCR is disabled"))

    def _is_glm_markdown_mode(self):
        engine = self.service.current_ocr_engine
        return (
            hasattr(engine, "name")
            and engine.name == "glm_ocr"
            and (self.service.stored_options is None
                 or self.service.stored_options.engine_options.get("output_markdown", True))
        )

    def onScanToTextFile(self, event):
        ocr_opts = self._get_ocr_options(from_cache=False, force_save=True)
        if ocr_opts is None:
            return
        use_markdown = self._is_glm_markdown_mode()
        ext = ".md" if use_markdown else ".txt"
        ext_label = _("Markdown") if use_markdown else _("Plain Text")
        filename = f"{self.view.reader.current_book.title}{ext}"
        saveExportedFD = wx.FileDialog(
            self.view,
            # Translators: the title of a save file dialog asking the user
            # for a filename to export notes to
            _("Save as"),
            defaultDir=wx.GetUserHome(),
            defaultFile=filename,
            wildcard=f"{ext_label} (*{ext})|*{ext}",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if saveExportedFD.ShowModal() != wx.ID_OK:
            return
        output_file = saveExportedFD.GetPath().strip()
        saveExportedFD.Destroy()
        if not output_file:
            return
        # Continue with OCR
        progress_dlg = RobustProgressDialog(
            self.view,
            # Translators: the title of a progress dialog
            _("Scanning Pages"),
            # Translators: the message of a progress dialog
            message=_("Preparing book"),
            maxvalue=len(self.service.reader.document),
            can_hide=True,
            can_abort=True,
        )
        self._continue_with_text_extraction(
            ocr_opts, output_file, progress_dlg, open_after=use_markdown
        )

    @call_threaded
    def _continue_with_text_extraction(
        self, ocr_opts, output_file, progress_dlg, open_after=False
    ):
        doc = self.service.reader.document
        total = len(doc)
        engine = self.service.current_ocr_engine

        # Smart batch path: GLM-OCR Cloud with text layer detection
        if (
            self._is_glm_markdown_mode()
            and hasattr(engine, "smart_batch_ocr")
            and hasattr(doc, "get_file_system_path")
        ):
            try:
                pdf_path = doc.get_file_system_path()
                if pdf_path and Path(pdf_path).suffix.lower() == ".pdf":
                    from bookworm.ocr_engines.glm_ocr import GlmOcrEngine  # noqa: PLC0415

                    def _progress(current, total_pages, message):
                        val = min(current + 1, total_pages)
                        wx.CallAfter(
                            progress_dlg.Update, val, message
                        )

                    md_text = GlmOcrEngine.smart_batch_ocr(
                        pdf_path, progress_callback=_progress
                    )
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(md_text)
                    progress_dlg.Dismiss()
                    if open_after:
                        wx.CallAfter(
                            self._open_ocr_result_file, output_file, total
                        )
                    else:
                        wx.CallAfter(
                            wx.MessageBox,
                            message=_(
                                "Successfully processed {total} pages.\n"
                                "Extracted text was written to: {file}"
                            ).format(total=total, file=output_file),
                            caption=_("OCR Completed"),
                            style=wx.ICON_INFORMATION | wx.OK,
                            parent=self.view,
                        )
                    return
            except Exception:
                log.exception(
                    "Smart batch OCR failed, falling back to per-page OCR."
                )

        # Standard path: per-page OCR
        args = (doc, output_file, ocr_opts)
        scan2text_process = QueueProcess(
            target=engine.scan_to_text, args=args
        )
        progress_dlg.set_abort_callback(scan2text_process.cancel)

        try:
            for progress in scan2text_process:
                progress_dlg.Update(
                    progress + 1,
                    f"Scanning page {progress} of {total}",
                )
            if open_after and Path(output_file).exists():
                wx.CallAfter(self._open_ocr_result_file, output_file, total)
            else:
                wx.CallAfter(
                    wx.MessageBox,
                    message=_(
                        "Successfully processed {total} pages.\n"
                        "Extracted text was written to: {file}"
                    ).format(total=total, file=output_file),
                    caption=_("OCR Completed"),
                    style=wx.ICON_INFORMATION | wx.OK,
                    parent=self.view,
                )
        finally:
            progress_dlg.Dismiss()
            wx.CallAfter(self.view.contentTextCtrl.SetFocus)

    def _open_ocr_result_file(self, output_file, total):
        retval = wx.MessageBox(
            _(
                "Successfully processed {total} pages.\n"
                "Open the result in Bookworm for structured navigation?"
            ).format(total=total),
            _("OCR Completed"),
            style=wx.YES_NO | wx.ICON_INFORMATION,
            parent=self.view,
        )
        if retval == wx.YES:
            uri = DocumentUri(
                format="markdown",
                path=output_file,
                openner_args={},
            )
            self.view.open_uri(uri)

    def onChangeOCROptions(self, event):
        self._get_ocr_options(from_cache=False)

    def onScanImageFile(self, event):
        wildcard = []
        all_exts = [
            ("*.png", _("Portable Network Graphics")),
            ("*.jpg", _("JPEG images")),
            ("*.bmp", _("Bitmap images")),
            ("*.tif", _("Tiff graphics")),
        ]
        for ext, name in all_exts:
            wildcard.append("{name} ({ext})|{ext}|".format(name=name, ext=ext))
        wildcard[-1] = wildcard[-1].rstrip("|")
        allfiles = ";".join(ext[0] for ext in all_exts)
        wildcard.insert(0, _("All supported image formats") + f"|{allfiles}|")
        openFileDlg = wx.FileDialog(
            self.view,
            # Translators: the title of a file dialog to browse to an image
            message=_("Choose image file"),
            defaultDir=str(Path.home()),
            wildcard="".join(wildcard),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        if openFileDlg.ShowModal() == wx.ID_OK:
            filename = openFileDlg.GetPath().strip()
            openFileDlg.Destroy()
            if not filename or not os.path.isfile(filename):
                return
            # Load the image file
            image = ImageIO.from_filename(filename)
            if image is None:
                wx.MessageBox(
                    # Translators: content of a message box
                    _(
                        "Could not load image from\n{filename}.\n"
                        "Please make sure the file exists and the data contained in is not corrupted."
                    ).format(filename=filename),
                    # Translators: title of a message box
                    _("Could not load image file"),
                    style=wx.ICON_ERROR,
                )
                return
            options = self._get_ocr_options_from_dlg(force_save=True)
            if not options:
                return

            def _ocr_callback(ocr_result):
                engine = self.service.current_ocr_engine
                use_markdown = (
                    hasattr(engine, "name")
                    and engine.name == "glm_ocr"
                    and ocr_request.engine_options.get("output_markdown", False)
                )
                if use_markdown:
                    doc_cls = _MarkdownOcrRecognitionResultsDocument
                    doc_format = _MarkdownOcrRecognitionResultsDocument.format
                else:
                    doc_cls = _ImageOcrRegonitionResultsDocument
                    doc_format = _ImageOcrRegonitionResultsDocument.format
                recog_uri = DocumentUri(
                    format=doc_format,
                    path=filename,
                    openner_args={},
                )
                recog_document = doc_cls(
                    recog_uri,
                    ocr_result=ocr_result,
                    image_name=Path(filename).stem,
                )
                recog_document.read()
                wx.CallAfter(self.view.load_document, recog_document)

            factor = options.zoom_factor
            resized_image = image.to_pil().resize(
                (factor * image.width, factor * image.height), resample=Image.LANCZOS
            )
            ocr_request = OcrRequest(
                languages=options.languages,
                image=ImageIO.from_pil(resized_image),
                image_processing_pipelines=options.image_processing_pipelines,
            )
            self._run_ocr(ocr_request, _ocr_callback)

    @gui_thread_safe
    def _process_ocr_result(self, callback, task):
        if self._ocr_cancelled.is_set():
            ocr_ended.send(sender=self.view, isfaulted=True)
            self._ocr_cancelled.clear()
            return
        try:
            ocr_result = task.result()
        except OcrAuthenticationError as e:
            ocr_ended.send(sender=self.view, isfaulted=True)
            wx.MessageBox(
                str(e), _("Authentication Error"), style=wx.ICON_ERROR, parent=self.view
            )
            return
        except OcrNetworkError as e:
            ocr_ended.send(sender=self.view, isfaulted=True)
            wx.MessageBox(
                str(e), _("Network Error"), style=wx.ICON_ERROR, parent=self.view
            )
            return
        except OcrProcessingError as e:
            ocr_ended.send(sender=self.view, isfaulted=True)
            wx.MessageBox(
                str(e), _("OCR Service Error"), style=wx.ICON_ERROR, parent=self.view
            )
            return
        except Exception as e:
            log.exception("An unexpected error occurred during OCR.")
            ocr_ended.send(sender=self.view, isfaulted=True)
            wx.MessageBox(
                _(
                    "An unexpected error occurred during OCR. Please check the logs for details."
                ),
                _("Error"),
                style=wx.ICON_ERROR,
                parent=self.view,
            )
            return
        callback(ocr_result)
        sounds.ocr_end.play()
        speech.announce(_("Scan finished."), urgent=True)
        self.view.contentTextCtrl.SetFocusFromKbd()
        ocr_ended.send(sender=self.view, isfaulted=False)

    def _on_ocr_cancelled(self):
        self._ocr_cancelled.set()
        speech.announce(_("OCR canceled"), True)
        sounds.ocr_end.play()
        return True

    def _on_reader_loaded(self, sender):
        can_render = sender.document.can_render_pages()
        for item_id in OCRMenuIds:
            self.Enable(item_id, can_render)

    def _on_reader_unloaded(self, sender):
        self.service.stored_options = None
        self.service.saved_scanned_pages.clear()
        self.auto_scan_item.Check(False)

    def _on_reader_page_changed(self, sender, current, prev):
        page_index = current.index if hasattr(current, "index") else current
        if page_index in self.service.saved_scanned_pages:
            cached = self.service.saved_scanned_pages[page_index]
            if isinstance(cached, tuple):
                self._set_content_with_semantics(cached[0], cached[1])
            else:
                self.view.set_content(cached)
        elif self.auto_scan_item.IsChecked():
            self.onScanCurrentPage(None)

    def on_should_auto_navigate_to_next_page(self, sender):
        return not self.auto_scan_item.IsChecked()
