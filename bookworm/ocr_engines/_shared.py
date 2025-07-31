import requests
import time
import threading

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


class StrictRateLimiter:
    """
    A strict, thread-safe rate limiter (throttle).
    It ensures that operations do not exceed a specified Queries Per Second (QPS) rate.
    """

    def __init__(self, qps: float):
        if qps <= 0:
            raise ValueError("QPS must be a positive number.")

        self._lock = threading.Lock()
        self.min_interval = 1.0 / qps
        self._next_allowed_time = time.monotonic()

    def wait_for_permission(self):
        """
        Blocks the current thread until the next operation is permitted.
        """
        with self._lock:
            now = time.monotonic()

            wait_time = self._next_allowed_time - now
            if wait_time > 0:
                time.sleep(wait_time)
                now = (
                    time.monotonic()
                )  # Re-evaluate 'now' after sleeping for better accuracy.

            # Determine the next allowed time.
            # Using max(now, self._next_allowed_time) prevents bursts of requests after an idle period.
            # It ensures the gate opens smoothly at the defined interval, not all at once.
            self._next_allowed_time = (
                max(now, self._next_allowed_time) + self.min_interval
            )
