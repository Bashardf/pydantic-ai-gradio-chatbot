"""Secret-Redaction."""

from __future__ import annotations

import re

_SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{10,}"), "sk-***REDACTED***"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9._\-]+", re.I), "Bearer ***REDACTED***"),
]


def redact_secrets(text: str) -> str:
    if not text:
        return text
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
