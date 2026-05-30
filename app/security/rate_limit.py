"""Rate-Limiting pro Aktion und Client/IP-Schlüssel."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from threading import Lock

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_PDF_PER_HOUR = int(os.getenv("RATE_LIMIT_PDF_REQUESTS", "5"))
RATE_LIMIT_PDF_WINDOW = int(os.getenv("RATE_LIMIT_PDF_WINDOW", "3600"))


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    def __init__(self, limits: dict[str, tuple[int, int]]) -> None:
        self._limits = limits
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, action: str, key: str = "global") -> None:
        bucket = f"{action}:{key}"
        if action not in self._limits:
            return
        max_calls, window = self._limits[action]
        now = time.monotonic()
        with self._lock:
            hits = self._hits[bucket]
            hits[:] = [t for t in hits if now - t < window]
            if len(hits) >= max_calls:
                wait = int(window - (now - hits[0])) + 1
                raise RateLimitExceeded(
                    f"Zu viele Anfragen. Bitte {wait} Sekunde(n) warten."
                )
            hits.append(now)


rate_limiter = RateLimiter(
    {
        "chat": (RATE_LIMIT_PER_MINUTE, RATE_LIMIT_WINDOW),
        "pdf_ingest": (RATE_LIMIT_PDF_PER_HOUR, RATE_LIMIT_PDF_WINDOW),
        "pdf_search": (RATE_LIMIT_PER_MINUTE, RATE_LIMIT_WINDOW),
    }
)
