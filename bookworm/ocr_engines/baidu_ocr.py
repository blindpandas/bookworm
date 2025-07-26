# -*- coding: utf-8 -*-

import base64
import json
from functools import lru_cache

import requests
from bookworm import config
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from bookworm.ocr_engines import BaseOcrEngine, OcrRequest, OcrResult

log = logger.getChild(__name__)

# Define constants for configuration keys
BAIDU_API_KEY_NAME = "baidu_api_key"
BAIDU_SECRET_KEY_NAME = "baidu_secret_key"


class _BaiduOcrBase(BaseOcrEngine):
    """
    Base class for Baidu OCR engines, handling common logic.
    """

    # Baidu OCR API does not support recognizing multiple languages at once.
    __supports_more_than_one_recognition_language__ = False

    # The specific API endpoint URL will be overridden in subclasses.
    url = ""

    @classmethod
    def check(cls) -> bool:
        """
        Checks if this engine is available. For a pure API engine,
        we assume it's always available. The check for API keys
        will happen at the time of recognition.
        """
        return True

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        """
        Returns a list of languages supported by Baidu OCR.
        Note: This list is based on Baidu's documentation and may need updates if the API changes.
        """
        return [
            LocaleInfo("zh-CN"),
            LocaleInfo("en"),
            LocaleInfo("ja"),
            LocaleInfo("ko"),
            LocaleInfo("fr"),
            LocaleInfo("es"),
            LocaleInfo("pt"),
            LocaleInfo("de"),
            LocaleInfo("it"),
            LocaleInfo("ru"),
        ]

    @classmethod
    @lru_cache(maxsize=1)
    def _get_access_token(cls) -> str | None:
        """
        Fetches the access_token from Baidu Cloud API.
        The token is cached as it's valid for 30 days.
        """
        conf = config.conf["ocr"]
        api_key = conf.get(BAIDU_API_KEY_NAME)
        api_secret = conf.get(BAIDU_SECRET_KEY_NAME)

        if not api_key or not api_secret:
            log.error("Baidu OCR API Key or Secret Key is not configured.")
            return None

        token_url = (
            "https://aip.baidubce.com/oauth/2.0/token"
            f"?grant_type=client_credentials&client_id={api_key}&client_secret={api_secret}"
        )
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            response = requests.post(token_url, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            access_token = response_data.get("access_token")
            if not access_token:
                log.error(f"Failed to get Baidu access_token: {response_data}")
                return None
            return access_token
        except requests.exceptions.RequestException as e:
            log.exception(f"Network error while getting Baidu access_token: {e}")
            return None
        except KeyError:
            log.exception(f"Unexpected response format from Baidu token endpoint.")
            return None

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """Performs the OCR recognition."""
        # The actual check for API keys is performed here, at the time of use.
        conf = config.conf["ocr"]
        if not conf.get(BAIDU_API_KEY_NAME) or not conf.get(BAIDU_SECRET_KEY_NAME):
            return OcrResult(
                recognized_text=_(
                    "Baidu OCR API Key and Secret Key are not configured. Please set them in Preferences > OCR."
                ),
                ocr_request=ocr_request,
            )

        access_token = cls._get_access_token()
        if not access_token:
            return OcrResult(
                recognized_text=_(
                    "Failed to authenticate with Baidu OCR. Please check if your API Key and Secret Key are correct."
                ),
                ocr_request=ocr_request,
            )

        image_bytes = ocr_request.image.as_bytes(format="PNG")
        b64_image = base64.b64encode(image_bytes)

        request_url = f"{cls.url}?access_token={access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"image": b64_image}

        try:
            response = requests.post(
                request_url, headers=headers, data=payload, timeout=20
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            log.exception(f"Failed to call Baidu OCR API: {e}")
            return OcrResult(
                recognized_text=_(
                    "A network error occurred while calling the Baidu OCR API."
                ),
                ocr_request=ocr_request,
            )

        if response_data.get("error_code"):
            error_msg = response_data.get("error_msg", _("Unknown error"))
            log.error(f"Baidu OCR API returned an error: {error_msg}")
            return OcrResult(
                recognized_text=_("Baidu OCR failed: ") + error_msg,
                ocr_request=ocr_request,
            )

        words_result = response_data.get("words_result", [])
        recognized_text = "\n".join([item.get("words", "") for item in words_result])

        return OcrResult(
            recognized_text=recognized_text,
            ocr_request=ocr_request,
        )


class BaiduGeneralOcrEngine(_BaiduOcrBase):
    """Baidu General OCR Engine (Standard version)."""

    # Translators: The name of an OCR engine
    name = "baidu_general_ocr"
    display_name = _("Baidu General OCR (Standard)")
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"


class BaiduAccurateOcrEngine(_BaiduOcrBase):
    """Baidu General OCR Engine (High-Precision version)."""

    # Translators: The name of an OCR engine
    name = "baidu_accurate_ocr"
    display_name = _("Baidu General OCR (Accurate)")
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
