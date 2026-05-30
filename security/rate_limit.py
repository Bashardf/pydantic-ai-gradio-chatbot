"""Einfaches In-Memory-Rate-Limiting pro Aktion."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from threading import Lock

RATE_LIMIT_CHAT_REQUESTS = int(os.getenv("RATE_LIMIT_CHAT_REQUESTS", "30"))
RATE_LIMIT_CHAT_WINDOW = int(os.getenv("RATE_LIMIT_CHAT_WINDOW", "60"))
RATE_LIMIT_PDF_REQUESTS = int(os.getenv("RATE_LIMIT_PDF_REQUESTS", "5"))
RATE_LIMIT_PDF_WINDOW = int(os.getenv("RATE_LIMIT_PDF_WINDOW", "3600"))


class RateLimitExceeded(Exception):
    """Zu viele Anfragen in kurzer Zeit."""


class RateLimiter:
    def __init__(self, limits: dict[str, tuple[int, int]]) -> None:
        self._limits = limits
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, action: str) -> None:
        if action not in self._limits:
            return
        max_calls, window_seconds = self._limits[action]
        now = time.monotonic()

        with self._lock:
            hits = self._hits[action]
            hits[:] = [t for t in hits if now - t < window_seconds]
            if len(hits) >= max_calls:
                wait = int(window_seconds - (now - hits[0])) + 1
                raise RateLimitExceeded(
                    f"Zu viele Anfragen. Bitte {wait} Sekunde(n) warten."
                )
            hits.append(now)


rate_limiter = RateLimiter(
    {
        "chat": (RATE_LIMIT_CHAT_REQUESTS, RATE_LIMIT_CHAT_WINDOW),
        "pdf_ingest": (RATE_LIMIT_PDF_REQUESTS, RATE_LIMIT_PDF_WINDOW),
        "pdf_search": (RATE_LIMIT_CHAT_REQUESTS, RATE_LIMIT_CHAT_WINDOW),
    }
)
