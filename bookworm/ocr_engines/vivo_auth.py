import json
import random
import string
import time
import urllib.parse
import requests
from functools import lru_cache

from bookworm.logger import logger
from .base import OcrAuthenticationError, OcrNetworkError
from ._shared import create_session_with_retries

log = logger.getChild(__name__)

# Constants
NVDACN_API_URL = "https://nvdacn.com/api/"
VIVO_APP_ID = "3046775094"

# Create a session specifically for authentication requests
auth_session = create_session_with_retries()


def _gen_nonce(length=8):
    """Generates a random alphanumeric string of a given length."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _gen_canonical_query_string(params):
    """Creates a sorted, URL-encoded query string for signature consistency."""
    if not params:
        return ""
    return "&".join(f"{k}={v}" for k, v in sorted(params.items()))


@lru_cache(maxsize=2)
def _fetch_signature_from_service(nvdacn_user, nvdacn_pass, signing_string_bytes):
    """Fetches the signature from the NVDACN API using a robust session."""
    api_params = {
        "user": nvdacn_user,
        "pass": nvdacn_pass,
        "name": "vivo",
        "action": "signature",
    }
    url = f"{NVDACN_API_URL}?{urllib.parse.urlencode(api_params)}"
    try:
        log.debug("Requesting Vivo signature from NVDA.cn API for user: %s", nvdacn_user)
        response = auth_session.post(url, data=signing_string_bytes, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("code") == 200 and "data" in result:
            log.info("Successfully fetched Vivo signature for user: %s", nvdacn_user)
            return result["data"]
        else:
            error_message = result.get("data", "Unknown API error")
            log.error(
                "NVDACN signature API returned a business error for user %s: %s (Code: %s)",
                nvdacn_user, error_message, result.get('code')
            )
            raise OcrAuthenticationError(
                f"NVDACN API Error: {error_message} (Code: {result.get('code')})"
            )
    except requests.exceptions.RequestException as e:
        log.error("Network error while fetching Vivo signature for user %s.", nvdacn_user, exc_info=True)
        raise OcrNetworkError("NVDACN API connection failed") from e
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise OcrAuthenticationError("Invalid response from NVDACN API") from e


def gen_sign_headers(nvdacn_user, nvdacn_pass, method, uri, query):
    """Generates the complete set of authentication headers for the VIVO API."""
    method = str(method).upper()
    timestamp = str(int(time.time()))
    nonce = _gen_nonce()
    canonical_query_string = _gen_canonical_query_string(query)
    signed_headers_string = (
        f"x-ai-gateway-app-id:{VIVO_APP_ID}\n"
        f"x-ai-gateway-timestamp:{timestamp}\n"
        f"x-ai-gateway-nonce:{nonce}"
    )
    signing_string = (
        f"{method}\n{uri}\n{canonical_query_string}\n"
        f"{VIVO_APP_ID}\n{timestamp}\n{signed_headers_string}"
    )
    signing_string_bytes = signing_string.encode("utf-8")
    signature = _fetch_signature_from_service(
        nvdacn_user, nvdacn_pass, signing_string_bytes
    )
    return {
        "X-AI-GATEWAY-APP-ID": VIVO_APP_ID,
        "X-AI-GATEWAY-TIMESTAMP": timestamp,
        "X-AI-GATEWAY-NONCE": nonce,
        "X-AI-GATEWAY-SIGNED-HEADERS": "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce",
        "X-AI-GATEWAY-SIGNATURE": signature,
    }
