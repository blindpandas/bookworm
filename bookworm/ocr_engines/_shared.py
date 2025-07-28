import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session_with_retries() -> requests.Session:
    """
    Creates a requests session with a robust retry strategy.
    """
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
