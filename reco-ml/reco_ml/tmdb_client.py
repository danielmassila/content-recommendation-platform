"""TMDB HTTP access, independent of persistence and orchestration.

Freshness/cache decisions belong to the caller; this client never writes data.
HTTP errors retain their status so callers can distinguish missing films from
authentication failures or temporary outages.
"""

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


TMDB_API_BASE_URL = "https://api.themoviedb.org/3"


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            delay = float(value)
        except ValueError:
            try:
                delay = (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
            except (ValueError, TypeError, OverflowError):
                return 2 ** attempt
        if math.isfinite(delay):
            return max(0, delay)
    return 2 ** attempt


class TmdbClient:
    def __init__(self, api_key: str, *, timeout: float = 15,
                 max_attempts: int = 3, language: str = "fr-FR"):
        if not api_key or not api_key.strip():
            raise ValueError("TMDB API key is required")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Timeout must be finite and positive")
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        self._api_key = api_key
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.language = language

    def get_movie(self, tmdb_id: int) -> dict:
        if type(tmdb_id) is not int or tmdb_id <= 0:
            raise ValueError("TMDB ID must be a positive integer")
        query = urllib.parse.urlencode({
            "api_key": self._api_key,
            "append_to_response": "credits",
            "language": self.language,
        })
        request = urllib.request.Request(
            f"{TMDB_API_BASE_URL}/movie/{tmdb_id}?{query}",
            headers={"Accept": "application/json", "User-Agent": "content-recommendation-platform/1.0"},
        )
        for attempt in range(self.max_attempts):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, dict) or type(payload.get("id")) is not int or payload["id"] != tmdb_id:
                    raise ValueError("TMDB response does not match the requested movie ID")
                return payload
            except urllib.error.HTTPError as error:
                retryable = error.code == 429 or 500 <= error.code < 600
                retry_after = error.headers.get("Retry-After") if error.headers else None
                error.close()
                if not retryable or attempt == self.max_attempts - 1:
                    raise
                time.sleep(_retry_delay(retry_after, attempt))
            except (urllib.error.URLError, TimeoutError):
                if attempt == self.max_attempts - 1:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("TMDB request ended without a response")
