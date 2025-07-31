# -*- coding: utf-8 -*-

import base64
import requests
from bookworm import config
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from .base import (
    BaseOcrEngine,
    EngineOption,
    OcrRequest,
    OcrResult,
    OcrAuthenticationError,
    OcrNetworkError,
    OcrProcessingError,
)
from ._shared import create_session_with_retries
from ._shared import StrictRateLimiter
from . import vivo_auth

log = logger.getChild(__name__)

# --- Constants for configuration and API interaction ---
VIVO_NVDACN_USER_CONFIG_KEY = "vivo_nvdacn_user"
VIVO_NVDACN_PASS_CONFIG_KEY = "vivo_nvdacn_pass"


class VivoOcrEngine(BaseOcrEngine):
    """
    Implements the Vivo General Text Recognition V2.0 API.
    """

    name = "vivo_ocr"
    display_name = _("Vivo General OCR")
    __supports_more_than_one_recognition_language__ = False

    # --- API constants, moved from methods to class level ---
    DOMAIN = "api-ai.vivo.com.cn"
    URI = "/ocr/general_recognition"
    # 1.0 provides a safe buffer for a 2 QPS limit.
    rate_limiter = StrictRateLimiter(qps=1.0)

    session = create_session_with_retries()

    @classmethod
    def check(cls) -> bool:
        """Always returns True. Credentials will be checked at recognition time."""
        return True

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        """Vivo's API is primarily for Chinese and English."""
        return [LocaleInfo("zh-CN"), LocaleInfo("en")]

    @classmethod
    def get_engine_options(cls) -> list[EngineOption]:
        """Returns configurable options for the Vivo engine."""
        return [
            EngineOption(
                key="businessid",
                label=_("Enable Enhanced Recognition (slower, supports rotation)"),
                default=True,
            ),
        ]

    @classmethod
    def _parse_recognition_result(cls, response_data: dict) -> str:
        """
        Parses the recognition result from the Vivo API response.
        """
        result = response_data.get("result", {})
        return "\n".join([item.get("words", "") for item in result.get("words", [])])

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """Performs the OCR recognition using the Vivo API."""
        conf = config.conf["ocr"]
        nvdacn_user = conf.get(VIVO_NVDACN_USER_CONFIG_KEY)
        nvdacn_pass = conf.get(VIVO_NVDACN_PASS_CONFIG_KEY)
        if not nvdacn_user or not nvdacn_pass:
            raise OcrAuthenticationError(
                _("NVDA.cn username and password for Vivo OCR are not configured.")
            )
        image_bytes = ocr_request.image.as_bytes(format="JPEG")
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        business_id = (
            "1990173156ceb8a09eee80c293135279"
            if ocr_request.engine_options.get("businessid", True)
            else "8bf312e702043779ad0f2760b37a0806"
        )
        post_data = {
            "image": image_b64,
            "pos": 0,
            "businessid": business_id,
        }
        cls.rate_limiter.wait_for_permission()
        log.info(
            "Starting Vivo OCR with options: %s",
            ocr_request.engine_options
        )
        try:
            headers = vivo_auth.gen_sign_headers(
                nvdacn_user, nvdacn_pass, "POST", cls.URI, {}
            )
        except (OcrAuthenticationError, OcrNetworkError) as e:
            raise e
        url = f"https://{cls.DOMAIN}{cls.URI}"
        try:
            response = cls.session.post(
                url, data=post_data, headers=headers, timeout=20
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            log.error("Network error while calling Vivo OCR API.", exc_info=True)
            raise OcrNetworkError(
                _("A network error occurred while calling the Vivo OCR API.")
            ) from e
        error_code = response_data.get("error_code")
        if error_code != 0:
            error_msg = response_data.get("error_msg", "Unknown API error")
            log.error(
                f"Vivo OCR API returned an error: {error_msg} (code: {error_code})"
            )
            raise OcrProcessingError(_("Vivo OCR failed: ") + error_msg)
        log.info("Successfully recognized using Vivo OCR.")
        recognized_text = cls._parse_recognition_result(response_data)
        return OcrResult(
            recognized_text=recognized_text,
            ocr_request=ocr_request,
        )
