"""HTTP client for SEC EDGAR with rate limiting and retry."""

import logging
import time

import requests

from ledgar.config import get_user_agent

log = logging.getLogger(__name__)

# SEC allows max 10 requests/second
MIN_REQUEST_INTERVAL = 0.1


class DownloadError(Exception):
    """HTTP or network failure during EDGAR fetch."""


class RateLimitError(DownloadError):
    """SEC rate limit hit (HTTP 429)."""


class EdgarClient:
    """HTTP client for SEC EDGAR APIs with rate limiting."""

    def __init__(self, user_agent: str | None = None):
        self.session = requests.Session()
        ua = user_agent or get_user_agent()
        self.session.headers.update({
            "User-Agent": ua,
            "Accept-Encoding": "gzip, deflate",
        })
        self._last_request_time = 0.0

    def _throttle(self) -> None:
        """Enforce SEC rate limit of 10 req/sec."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.monotonic()

    def fetch_json(self, url: str, retries: int = 3) -> dict:
        """Fetch a JSON resource from SEC EDGAR with retry."""
        last_exc = None
        for attempt in range(1, retries + 1):
            self._throttle()
            log.debug("GET %s (attempt %d/%d)", url, attempt, retries)
            try:
                resp = self.session.get(url, timeout=30)
            except requests.RequestException as exc:
                last_exc = DownloadError(f"Network error fetching {url}: {exc}")
                log.warning("Attempt %d failed: %s", attempt, exc)
                time.sleep(2**attempt)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "10"))
                log.warning("Rate limited. Waiting %d seconds...", retry_after)
                time.sleep(retry_after)
                last_exc = RateLimitError(f"Rate limited on {url}")
                continue

            if resp.status_code != 200:
                last_exc = DownloadError(
                    f"HTTP {resp.status_code} fetching {url}"
                )
                log.warning("Attempt %d: HTTP %d", attempt, resp.status_code)
                time.sleep(2**attempt)
                continue

            return resp.json()

        raise last_exc  # type: ignore[misc]

    def fetch_bytes(self, url: str, retries: int = 3, stream: bool = False):
        """Fetch raw bytes from SEC EDGAR with retry. Returns response object if stream=True."""
        last_exc = None
        for attempt in range(1, retries + 1):
            self._throttle()
            log.debug("GET %s (attempt %d/%d, stream=%s)", url, attempt, retries, stream)
            try:
                resp = self.session.get(url, timeout=120, stream=stream)
            except requests.RequestException as exc:
                last_exc = DownloadError(f"Network error fetching {url}: {exc}")
                log.warning("Attempt %d failed: %s", attempt, exc)
                time.sleep(2**attempt)
                continue

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "10"))
                log.warning("Rate limited. Waiting %d seconds...", retry_after)
                time.sleep(retry_after)
                last_exc = RateLimitError(f"Rate limited on {url}")
                continue

            if resp.status_code != 200:
                last_exc = DownloadError(
                    f"HTTP {resp.status_code} fetching {url}"
                )
                log.warning("Attempt %d: HTTP %d", attempt, resp.status_code)
                time.sleep(2**attempt)
                continue

            if stream:
                return resp
            return resp.content

        raise last_exc  # type: ignore[misc]
