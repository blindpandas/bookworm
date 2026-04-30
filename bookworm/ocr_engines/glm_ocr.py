"""
GLM-OCR Engine integration.

Supports three deployment modes:
  - cloud:  Zhipu layout_parsing API ($0.03/M tokens, no GPU needed)
  - ollama: Local Ollama server (free, no GPU required, ~1.6GB model)
  - local:  glmocr Python package with self-hosted model (needs CUDA GPU)

Cloud mode supports direct PDF upload (up to 100 pages, 50MB) for
batch processing in a single request — no per-page image rendering needed.
"""

from __future__ import annotations

import base64
import json
import re
import time
from enum import Enum
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bookworm import config
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger

from ._shared import StrictRateLimiter
from .base import (
    BaseOcrEngine,
    EngineOption,
    OcrAuthenticationError,
    OcrNetworkError,
    OcrProcessingError,
    OcrRequest,
    OcrResult,
)

log = logger.getChild(__name__)

GLM_OCR_API_KEY_CONFIG_KEY = "glm_ocr_api_key"
GLM_OCR_MODE_CONFIG_KEY = "glm_ocr_mode"
GLM_OCR_OLLAMA_HOST_CONFIG_KEY = "glm_ocr_ollama_host"

GLM_OCR_LAYOUT_PARSING_URL = "https://open.bigmodel.cn/api/paas/v4/layout_parsing"
GLM_OCR_MODEL_NAME = "glm-ocr"
GLM_OCR_DEFAULT_OLLAMA_HOST = "http://localhost:11434"

# ── Post-processing pipeline (inspired by 42md) ──

_POSTPROCESS_RULES = [
    (re.compile(r"(&nbsp;){3,}"), " "),
    (re.compile(r"(?m)^\[(\d+)\](:\s*.+)$"), r"[^\1]\2"),
    (re.compile(r"\$\s*\^\{(\d+)\}\s*\$"), r"[^\1]"),
    (re.compile(r"\n{4,}"), "\n\n\n"),
    (re.compile(r"[ \t]+$", re.MULTILINE), ""),
    (re.compile(r"^(#{1,6})\s*\*{1,2}(.+?)\*{1,2}\s*$", re.MULTILINE), r"\1 \2"),
]


def postprocess_markdown(text: str) -> str:
    """Clean up raw OCR Markdown output."""
    for pattern, replacement in _POSTPROCESS_RULES:
        text = pattern.sub(replacement, text)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped in ("```", "```markdown"):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


class GlmOcrMode(str, Enum):
    CLOUD = "cloud"
    OLLAMA = "ollama"
    LOCAL = "local"

class GlmOcrEngine(BaseOcrEngine):
    """GLM-OCR engine with table, formula, and layout recognition."""

    name = "glm_ocr"
    display_name = _("GLM-OCR (Zhipu)")
    __supports_more_than_one_recognition_language__ = False
    __requires_rate_limiting__ = True

    rate_limiter = StrictRateLimiter(qps=0.5)
    session = requests.Session()
    session.trust_env = False
    _retry_adapter = HTTPAdapter(max_retries=Retry(
        total=3,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
    ))
    session.mount("https://", _retry_adapter)
    session.mount("http://", _retry_adapter)

    @classmethod
    def check(cls) -> bool:
        return True

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        return [
            LocaleInfo("zh-CN"),
            LocaleInfo("en"),
            LocaleInfo("ja"),
            LocaleInfo("ko"),
            LocaleInfo("fr"),
            LocaleInfo("de"),
            LocaleInfo("es"),
            LocaleInfo("ru"),
        ]

    @classmethod
    def get_engine_options(cls) -> list[EngineOption]:
        return [
            EngineOption(
                key="output_markdown",
                label=_("Output structured Markdown (tables, formulas)"),
                default=True,
            ),
        ]

    @classmethod
    def _get_mode(cls) -> GlmOcrMode:
        conf = config.conf["ocr"]
        mode = conf.get(GLM_OCR_MODE_CONFIG_KEY, GlmOcrMode.CLOUD.value)
        try:
            return GlmOcrMode(mode)
        except ValueError:
            return GlmOcrMode.CLOUD

    @classmethod
    def _get_api_key(cls) -> str:
        conf = config.conf["ocr"]
        api_key = conf.get(GLM_OCR_API_KEY_CONFIG_KEY, "")
        if not api_key:
            raise OcrAuthenticationError(
                _("GLM-OCR API key is not configured. Please set it in OCR settings.")
            )
        return api_key

    @classmethod
    def _get_ollama_host(cls) -> str:
        conf = config.conf["ocr"]
        return (
            conf.get(GLM_OCR_OLLAMA_HOST_CONFIG_KEY, "")
            or GLM_OCR_DEFAULT_OLLAMA_HOST
        )

    # ── Cloud mode: single image ──

    @classmethod
    def _recognize_cloud(cls, ocr_request: OcrRequest) -> str:
        """Call Zhipu layout_parsing with a single page image."""
        api_key = cls._get_api_key()
        image_bytes = ocr_request.image.as_bytes(format="PNG")
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": GLM_OCR_MODEL_NAME,
            "file": f"data:image/png;base64,{b64_image}",
        }
        return cls._cloud_request(api_key, payload)

    @classmethod
    def recognize_single_page_pdf(cls, pdf_path: str | Path, page_number: int) -> str:
        """Extract one page as a temp PDF and upload it. No size limit issues."""
        import tempfile  # noqa: PLC0415

        import fitz  # noqa: PLC0415

        api_key = cls._get_api_key()
        src = fitz.open(str(pdf_path))
        tmp = fitz.open()
        tmp.insert_pdf(src, from_page=page_number, to_page=page_number)

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as f:
            tmp_path = f.name
        tmp.save(tmp_path)
        tmp.close()
        src.close()

        try:
            pdf_bytes = Path(tmp_path).read_bytes()
            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            payload = {
                "model": GLM_OCR_MODEL_NAME,
                "file": f"data:application/pdf;base64,{b64_pdf}",
            }
            log.info(
                "GLM-OCR single-page PDF: page %d, %d bytes",
                page_number,
                len(pdf_bytes),
            )
            return cls._cloud_request(api_key, payload)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # ── Cloud mode: direct PDF upload (batch, up to 100 pages) ──

    MAX_PDF_SIZE = 50 * 1024 * 1024

    @classmethod
    def recognize_pdf_file(
        cls,
        pdf_path: str | Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> str:
        """Upload entire PDF to Zhipu for batch OCR. Returns full Markdown."""
        api_key = cls._get_api_key()
        pdf_path = Path(pdf_path)
        if pdf_path.stat().st_size > cls.MAX_PDF_SIZE:
            raise OcrProcessingError(
                _("PDF file exceeds 50MB limit for direct upload.")
            )
        pdf_bytes = pdf_path.read_bytes()
        b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

        payload = {
            "model": GLM_OCR_MODEL_NAME,
            "file": f"data:application/pdf;base64,{b64_pdf}",
        }
        if start_page is not None:
            payload["start_page_id"] = start_page
        if end_page is not None:
            payload["end_page_id"] = end_page

        log.info(
            "GLM-OCR PDF upload: %d bytes, pages %s-%s",
            len(pdf_bytes),
            start_page or 1,
            end_page or "end",
        )
        return cls._cloud_request(api_key, payload)

    # ── Smart batch OCR for large PDFs ──

    BATCH_CHUNK_SIZE = 50
    TEXT_LAYER_MIN_CHARS = 50

    @classmethod
    def smart_batch_ocr(cls, pdf_path: str | Path, progress_callback=None):
        """Fast batch OCR: detect text layers locally, OCR only scanned pages.

        Yields nothing; calls progress_callback(current, total, message).
        Returns full Markdown string with all pages merged.
        """
        import fitz  # noqa: PLC0415

        pdf_path = Path(pdf_path)
        src = fitz.open(str(pdf_path))
        total = len(src)
        results = {}
        ocr_needed = []

        for i in range(total):
            page = src[i]
            text = page.get_text("text").strip()
            if len(text) >= cls.TEXT_LAYER_MIN_CHARS:
                extracted = cls._fitz_page_to_markdown(page, text)
                if len(extracted.strip()) >= cls.TEXT_LAYER_MIN_CHARS:
                    results[i] = extracted
                else:
                    ocr_needed.append(i)
            else:
                ocr_needed.append(i)
            if progress_callback:
                progress_callback(
                    i, total, _("Analyzing page {n}/{total}").format(
                        n=i + 1, total=total
                    )
                )

        log.info(
            "Smart batch: %d pages with text layer, %d need OCR",
            len(results), len(ocr_needed),
        )

        if not ocr_needed:
            src.close()
            return cls._merge_results(results, total)

        cls._parallel_ocr_chunks(
            src, ocr_needed, results, total, len(results), progress_callback
        )
        src.close()
        return cls._merge_results(results, total)

    @classmethod
    def _parallel_ocr_chunks(
        cls, src, ocr_needed, results, total, base_done, progress_callback
    ):
        from concurrent.futures import ThreadPoolExecutor, as_completed  # noqa: PLC0415

        chunks = [
            ocr_needed[i:i + cls.BATCH_CHUNK_SIZE]
            for i in range(0, len(ocr_needed), cls.BATCH_CHUNK_SIZE)
        ]
        completed_pages = base_done

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {}
            for chunk_idx, chunk_pages in enumerate(chunks):
                future = pool.submit(cls._ocr_chunk, src, chunk_pages)
                futures[future] = (chunk_idx, chunk_pages)
                time.sleep(1.5)

            for future in as_completed(futures):
                chunk_idx, chunk_pages = futures[future]
                try:
                    chunk_md = future.result()
                    page_texts = cls._split_chunk_result(
                        chunk_md, len(chunk_pages)
                    )
                    for j, page_idx in enumerate(chunk_pages):
                        results[page_idx] = (
                            page_texts[j] if j < len(page_texts) else ""
                        )
                except Exception:
                    log.exception(
                        "Batch chunk %d failed, skipping %d pages.",
                        chunk_idx, len(chunk_pages),
                    )
                    for page_idx in chunk_pages:
                        results[page_idx] = ""

                completed_pages += len(chunk_pages)
                if progress_callback:
                    progress_callback(
                        min(completed_pages, total - 1), total,
                        _("OCR: {done}/{total} pages").format(
                            done=completed_pages, total=total
                        ),
                    )

    @classmethod
    def _fitz_page_to_markdown(cls, page, plain_text: str) -> str:
        parts = []
        tables = page.find_tables()
        table_rects = [t.bbox for t in tables.tables] if tables.tables else []
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
                    if not text:
                        continue
                    max_size = max(
                        (s["size"] for s in line["spans"]), default=0
                    )
                    is_bold = any(
                        "bold" in s["font"].lower() for s in line["spans"]
                    )
                    if max_size > 16 and is_bold:
                        parts.append(f"## {text}")
                    elif max_size > 14 and is_bold:
                        parts.append(f"### {text}")
                    else:
                        parts.append(text)
        if tables.tables:
            parts.extend(t.to_markdown() for t in tables.tables)
        return postprocess_markdown("\n\n".join(parts)) if parts else plain_text

    @classmethod
    def _ocr_chunk(cls, src_doc, page_indices: list[int]) -> str:
        import tempfile  # noqa: PLC0415

        import fitz  # noqa: PLC0415

        api_key = cls._get_api_key()
        tmp_doc = fitz.open()
        for idx in page_indices:
            tmp_doc.insert_pdf(src_doc, from_page=idx, to_page=idx)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            tmp_path = f.name
        tmp_doc.save(tmp_path)
        tmp_doc.close()

        try:
            pdf_bytes = Path(tmp_path).read_bytes()
            if len(pdf_bytes) > cls.MAX_PDF_SIZE:
                Path(tmp_path).unlink(missing_ok=True)
                mid = len(page_indices) // 2
                left = cls._ocr_chunk(src_doc, page_indices[:mid])
                right = cls._ocr_chunk(src_doc, page_indices[mid:])
                return left + "\n\n" + right

            b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            payload = {
                "model": GLM_OCR_MODEL_NAME,
                "file": f"data:application/pdf;base64,{b64_pdf}",
            }
            log.info(
                "Smart batch chunk: %d pages, %d bytes",
                len(page_indices), len(pdf_bytes),
            )
            return cls._cloud_request(api_key, payload)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _split_chunk_result(md_text: str, expected_pages: int) -> list[str]:
        import re as _re  # noqa: PLC0415
        parts = _re.split(r"<!--\s*page\s+\d+\s*-->", md_text)
        parts = [postprocess_markdown(p) for p in parts if p.strip()]
        if len(parts) == expected_pages:
            return parts
        if len(parts) == 1 and expected_pages > 1:
            return [postprocess_markdown(md_text)]
        return parts

    @staticmethod
    def _merge_results(results: dict[int, str], total: int) -> str:
        sections = []
        for i in range(total):
            text = results.get(i, "")
            sections.append(f"<!-- page {i + 1} -->\n\n{text}")
        return "\n\n".join(sections)

    MAX_RETRIES_429 = 5

    @classmethod
    def _cloud_request(cls, api_key: str, payload: dict) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        for attempt in range(cls.MAX_RETRIES_429 + 1):
            cls.rate_limiter.wait_for_permission()
            try:
                response = cls.session.post(
                    GLM_OCR_LAYOUT_PARSING_URL,
                    headers=headers,
                    json=payload,
                    timeout=300,
                )
                if response.status_code == 429:
                    wait = min(2 ** attempt * 2, 30)
                    log.warning(
                        "GLM-OCR 429 rate limited, waiting %ds (attempt %d/%d)",
                        wait, attempt + 1, cls.MAX_RETRIES_429,
                    )
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                return cls._parse_layout_response(response)
            except Exception as e:
                if attempt < cls.MAX_RETRIES_429:
                    resp = getattr(e, "response", None)
                    if resp is not None and resp.status_code == 429:
                        wait = min(2 ** attempt * 2, 30)
                        log.warning("GLM-OCR 429, backoff %ds", wait)
                        time.sleep(wait)
                        continue
                log.exception("GLM-OCR cloud request failed.")
                cls._raise_network_error(e)
        cls._raise_network_error(
            OcrProcessingError("Max retries exceeded for 429")
        )
        return ""  # unreachable, _raise_network_error always raises

    # PLACEHOLDER_PARSE_AND_MODES

    @classmethod
    def _parse_layout_response(cls, response) -> str:
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            log.exception("Failed to decode GLM-OCR response.")
            raise OcrProcessingError(
                _("Failed to parse GLM-OCR API response.")
            ) from e

        if "error" in data or "code" in data:
            msg = (
                data.get("error", {}).get("message", "")
                or data.get("message", "")
            )
            log.error("GLM-OCR API error: %s", msg)
            raise OcrProcessingError(_("GLM-OCR API error: ") + msg)

        md_results = data.get("md_results", "")
        if md_results:
            return postprocess_markdown(md_results)

        details = data.get("layout_details", [])
        if details:
            raw = "\n\n".join(
                item.get("content", "")
                for item in details
                if item.get("content")
            )
            return postprocess_markdown(raw)

        log.warning("GLM-OCR returned empty result: %s", data)
        return ""

    # ── Ollama mode ──

    @classmethod
    def _recognize_ollama(cls, ocr_request: OcrRequest) -> str:
        host = cls._get_ollama_host()
        image_bytes = ocr_request.image.as_bytes(format="PNG")
        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {
            "model": GLM_OCR_MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": "Perform OCR on this image. "
                    "Output Markdown with tables and formulas preserved.",
                    "images": [b64_image],
                }
            ],
            "stream": False,
        }

        api_url = f"{host.rstrip('/')}/api/chat"
        try:
            response = cls.session.post(api_url, json=payload, timeout=180)
            response.raise_for_status()
        except Exception as e:
            if "Connection" in type(e).__name__:
                raise OcrNetworkError(
                    _(
                        "Cannot connect to Ollama at {host}. "
                        "Please ensure Ollama is running (ollama serve) "
                        "and the glm-ocr model is pulled (ollama pull glm-ocr)."
                    ).format(host=host)
                ) from e
            raise OcrNetworkError(
                _("Error communicating with Ollama: {error}").format(
                    error=str(e)
                )
            ) from e

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            log.exception("Failed to decode Ollama response.")
            raise OcrProcessingError(
                _("Failed to parse Ollama response.")
            ) from e

        if "error" in data:
            error_msg = data["error"]
            if "not found" in error_msg.lower():
                raise OcrProcessingError(
                    _(
                        "Model glm-ocr not found in Ollama. "
                        "Please run: ollama pull glm-ocr"
                    )
                )
            raise OcrProcessingError(
                _("Ollama error: {error}").format(error=error_msg)
            )

        try:
            return postprocess_markdown(data["message"]["content"])
        except KeyError as e:
            log.exception("Unexpected Ollama response: %s", data)
            raise OcrProcessingError(
                _("Failed to parse Ollama response.")
            ) from e

    # ── Local mode ──

    @classmethod
    def _recognize_local(cls, ocr_request: OcrRequest) -> str:
        try:
            from glmocr import GlmOcr  # noqa: PLC0415
        except ImportError as exc:
            raise OcrProcessingError(
                _(
                    "The glmocr package is not installed. "
                    "Please install it with: pip install glmocr[selfhosted]"
                )
            ) from exc

        image_pil = ocr_request.image.to_pil()
        try:
            with GlmOcr() as parser:
                result = parser.parse(image_pil)
                raw = (
                    result.markdown
                    if hasattr(result, "markdown")
                    else str(result)
                )
                return postprocess_markdown(raw)
        except Exception as e:
            log.exception("GLM-OCR local recognition failed.")
            raise OcrProcessingError(
                _("GLM-OCR local recognition failed: {error}").format(
                    error=str(e)
                )
            ) from e

    # ── Shared helpers ──

    @classmethod
    def _raise_network_error(cls, exc: Exception):
        if hasattr(exc, "response") and exc.response is not None:
            status = exc.response.status_code
            if status == 401:
                raise OcrAuthenticationError(
                    _("GLM-OCR API key is invalid or expired.")
                ) from exc
            if status == 429:
                raise OcrProcessingError(
                    _(
                        "GLM-OCR API quota exceeded. "
                        "Please top up your Zhipu account."
                    )
                ) from exc
            try:
                data = exc.response.json()
                msg = (
                    data.get("error", {}).get("message", "")
                    or data.get("message", "")
                )
                if msg:
                    raise OcrProcessingError(
                        _("GLM-OCR API error: ") + msg
                    ) from exc
            except (ValueError, AttributeError):
                pass
        raise OcrNetworkError(
            _("A network error occurred while calling the GLM-OCR API.")
        ) from exc

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """Perform OCR using GLM-OCR in the configured mode."""
        cls.rate_limiter.wait_for_permission()
        mode = cls._get_mode()

        if mode == GlmOcrMode.OLLAMA:
            recognized_text = cls._recognize_ollama(ocr_request)
        elif mode == GlmOcrMode.LOCAL:
            recognized_text = cls._recognize_local(ocr_request)
        else:
            recognized_text = cls._recognize_cloud(ocr_request)

        return OcrResult(
            recognized_text=recognized_text,
            ocr_request=ocr_request,
        )
