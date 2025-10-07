# -*- coding: utf-8 -*-

import base64
import json
from functools import lru_cache

import requests
from bookworm import config
from bookworm.i18n import LocaleInfo
from bookworm.logger import logger
from .base import (
    BaseOcrEngine,
    EngineOption,
    OcrRequest,
    OcrResult,
    OcrError,
    OcrAuthenticationError,
    OcrNetworkError,
    OcrProcessingError,
)
from ._shared import StrictRateLimiter
from ._shared import create_session_with_retries


log = logger.getChild(__name__)

# Define constants for configuration keys
BAIDU_API_KEY_NAME = "baidu_api_key"
BAIDU_SECRET_KEY_NAME = "baidu_secret_key"


class _BaiduOcrBase(BaseOcrEngine):
    """
    Base class for Baidu OCR engines, handling common logic.
    """

    __supports_more_than_one_recognition_language__ = False
    url = ""
    # 0.8 provides a safe buffer for a 2 QPS limit.
    rate_limiter = StrictRateLimiter(qps=0.8)

    # A comprehensive map of Bookworm's language codes to Baidu's API codes.
    # This includes all languages supported by the accurate version.
    # Subclasses can select from this map.
    LANG_CODE_MAP = {
        "zh": "CHN_ENG",
        "en": "ENG",
        "ja": "JAP",
        "ko": "KOR",
        "fr": "FRE",
        "es": "SPA",
        "pt": "POR",
        "de": "GER",
        "it": "ITA",
        "ru": "RUS",
        "da": "DAN",
        "nl": "DUT",
        "ms": "MAL",
        "sv": "SWE",
        "id": "IND",
        "pl": "POL",
        "ro": "ROM",
        "tr": "TUR",
        "el": "GRE",
        "hu": "HUN",
        "th": "THA",
        "vi": "VIE",
        "ar": "ARA",
        "hi": "HIN",
    }

    session = create_session_with_retries()

    @classmethod
    def check(cls) -> bool:
        """
        Always returns True for API-based engines.
        Actual availability is checked during the recognition process.
        """
        return True

    @classmethod
    def get_engine_options(cls) -> list[EngineOption]:
        """Returns the list of options supported by Baidu OCR engines."""
        return [
            EngineOption(
                key="detect_direction",
                label=_("Auto-detect and correct image direction"),
                default=True,
            ),
            EngineOption(
                key="paragraph",
                label=_("Attempt to reconstruct paragraphs"),
                default=True,
            ),
            EngineOption(
                key="multidirectional_recognize",
                label=_("Recognize text with multiple directions"),
                # This option is only supported by the accurate engine
                is_supported=lambda engine: engine.name == "baidu_accurate_ocr",
            ),
        ]

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        """Returns a list of languages supported by Baidu OCR."""
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
    def _fetch_and_cache_token(cls, api_key: str, api_secret: str) -> str:
        """
        Internal method that performs the network request to get the token.
        This method is cached based on api_key and api_secret.
        It either returns a valid token string (which gets cached) or raises an exception.
        """
        if not api_key or not api_secret:
            raise OcrAuthenticationError("API Key or Secret Key is not configured.")
        log.debug("Requesting new Baidu access token.")
        token_url = (
            "https://aip.baidubce.com/oauth/2.0/token"
            f"?grant_type=client_credentials&client_id={api_key}&client_secret={api_secret}"
        )
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        try:
            response = cls.session.post(token_url, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            access_token = response_data.get("access_token")
            if not access_token:
                log.error(
                    f"Failed to get Baidu access_token from response: {response_data}"
                )
                raise OcrAuthenticationError("Invalid API Key or Secret Key.")
            log.debug("Successfully fetched Baidu access token.")
            return access_token
        except requests.exceptions.RequestException as e:
            log.exception("Network request for Baidu access token failed.")
            raise OcrNetworkError(
                _(
                    "Could not get Baidu access token. Please check your network connection and ensure your API Key and Secret Key are correct."
                )
            ) from e
        except (KeyError, json.JSONDecodeError) as e:
            log.exception("Failed to parse Baidu access token response.")
            raise OcrProcessingError(
                "Received an invalid response from Baidu token endpoint."
            ) from e

    @classmethod
    def _get_access_token(cls) -> str:
        """
        Gets the access_token, utilizing a cache sensitive to API key changes.
        If fetching fails, it clears the cache for that specific key combination and re-raises the exception.
        """
        conf = config.conf["ocr"]
        api_key = conf.get(BAIDU_API_KEY_NAME)
        api_secret = conf.get(BAIDU_SECRET_KEY_NAME)
        try:
            log.debug(
                "Attempting to get Baidu access token (from cache or new request)."
            )
            return cls._fetch_and_cache_token(api_key, api_secret)
        except OcrError as e:
            log.warning(f"Clearing token cache due to a fetch error: {e}")
            cls._fetch_and_cache_token.cache_clear()
            raise

    @classmethod
    def _parse_recognition_result(
        cls, response_data: dict, ocr_request: OcrRequest
    ) -> str:
        """
        Parses the recognition result from the Baidu API response.
        If paragraph information is available and requested, it uses it to reconstruct paragraphs.
        Otherwise, it falls back to joining individual lines.
        """
        all_lines = response_data.get("words_result", [])
        # Check if the user requested paragraph info AND if the API returned it
        if (
            ocr_request.engine_options.get("paragraph")
            and "paragraphs_result" in response_data
        ):
            log.debug("Parsing recognition result using paragraph information.")
            paragraphs_info = response_data.get("paragraphs_result", [])
            reconstructed_paragraphs = []
            for para_info in paragraphs_info:
                # Get the indices of the lines belonging to this paragraph
                line_indices = para_info.get("words_result_idx", [])
                # Join the words of these lines with a space, not a newline
                paragraph_text = "".join(
                    all_lines[i].get("words", "").strip()
                    for i in line_indices
                    if i < len(all_lines)
                )
                reconstructed_paragraphs.append(paragraph_text)
            # Join the reconstructed paragraphs with newlines to separate them
            return "\n".join(reconstructed_paragraphs)
        else:
            # Fallback to the simple line-by-line joining method
            log.debug("Parsing recognition result by joining lines.")
            return "\n".join([item.get("words", "") for item in all_lines])

    @classmethod
    def recognize(cls, ocr_request: OcrRequest) -> OcrResult:
        """
        Performs the OCR recognition.
        Raises specific exceptions on failure.
        """
        # This will raise OcrAuthenticationError if keys are missing or invalid,
        # or OcrNetworkError on connection issues.
        cls.rate_limiter.wait_for_permission()
        access_token = cls._get_access_token()

        image_bytes = ocr_request.image.as_bytes(format="PNG")
        b64_image = base64.b64encode(image_bytes)

        payload = {
            "image": b64_image,
        }

        # Add language type
        selected_language = ocr_request.language
        if selected_language.given_locale_name == "auto_detect":
            payload["language_type"] = "auto_detect"
        else:
            lang_code = selected_language.two_letter_language_code
            payload["language_type"] = cls.LANG_CODE_MAP.get(lang_code, "CHN_ENG")

        # Add boolean options dynamically from the generic options dictionary
        for key, value in ocr_request.engine_options.items():
            if value:  # Only add if the user checked the box
                payload[key] = "true"

        log.debug(
            "Sending Baidu OCR request with payload: %s",
            {k: v for k, v in payload.items() if k != "image"},
        )

        request_url = f"{cls.url}?access_token={access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = cls.session.post(
                request_url, headers=headers, data=payload, timeout=20
            )
            response.raise_for_status()
            response_data = response.json()
        except requests.exceptions.RequestException as e:
            raise OcrNetworkError(
                _("A network error occurred while calling the Baidu OCR API.")
            ) from e

        if "error_code" in response_data:
            error_msg = response_data.get("error_msg", "Unknown API error")
            log.error(f"Baidu OCR API returned an error: {error_msg}")
            raise OcrProcessingError(_("Baidu OCR failed: ") + error_msg)
        # Only on success, process the result
        words_result = response_data.get("words_result", [])
        recognized_text = cls._parse_recognition_result(response_data, ocr_request)
        return OcrResult(
            recognized_text=recognized_text,
            ocr_request=ocr_request,
        )


class BaiduGeneralOcrEngine(_BaiduOcrBase):
    """Baidu General OCR Engine (Standard version)."""

    name = "baidu_general_ocr"
    display_name = _("Baidu General OCR (Standard)")
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"

    # Override the language map to reflect the limited set of the standard version.
    LANG_CODE_MAP = {
        "zh": "CHN_ENG",
        "en": "ENG",
        "ja": "JAP",
        "ko": "KOR",
        "fr": "FRE",
        "es": "SPA",
        "pt": "POR",
        "de": "GER",
        "it": "ITA",
        "ru": "RUS",
    }

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        """Returns the exact list of languages supported by the standard version."""
        return [LocaleInfo(lang_code) for lang_code in cls.LANG_CODE_MAP.keys()]


class BaiduAccurateOcrEngine(_BaiduOcrBase):
    """Baidu General OCR Engine (High-Precision version)."""

    name = "baidu_accurate_ocr"
    display_name = _("Baidu General OCR (Accurate)")
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"

    class _AutoDetectLocale(LocaleInfo):
        """
        A specialized LocaleInfo subclass to represent the 'Auto Detect' option.
        """

        def __init__(self):
            # Initialize with a valid locale ('en') to satisfy the parent constructor.
            # The actual locale doesn't matter as we override the necessary properties.
            super().__init__("en")
            # This is the unique identifier our `recognize` method will look for.
            self.given_locale_name = "auto_detect"

        @property
        def description(self) -> str:
            """Override the description to provide the desired UI text."""
            # Translators: An option in the OCR language list to automatically detect the language.
            return _("Auto Detect")

    @classmethod
    def get_recognition_languages(cls) -> list[LocaleInfo]:
        """
        Returns the list of languages supported by the accurate version,
        including a special option for auto-detection.
        """
        # Create an instance of our special subclass.
        auto_detect_lang = cls._AutoDetectLocale()
        # Get all specific languages from the map.
        specific_languages = [
            LocaleInfo(lang_code) for lang_code in cls.LANG_CODE_MAP.keys()
        ]
        # Return "Auto Detect" as the first option in the list.
        return [auto_detect_lang] + specific_languages
