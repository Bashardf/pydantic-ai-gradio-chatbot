"""Secret-Redaction – Keys dürfen nie in Logs oder UI erscheinen."""

from __future__ import annotations

import re

# OpenAI-Keys, Bearer-Tokens, typische Platzhalter
_SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{10,}"), "sk-***REDACTED***"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9._\-]+", re.I), "Bearer ***REDACTED***"),
    (re.compile(r"api[_-]?key[\"']?\s*[:=]\s*[\"']?[\w-]+", re.I), "api_key=***REDACTED***"),
]


def redact_secrets(text: str) -> str:
    """Entfernt erkannte Secrets aus Fehlermeldungen."""
    if not text:
        return text
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def mask_key_preview(key: str) -> str:
    """Zeigt nur die ersten/letzten Zeichen für Debug-Logs."""
    if len(key) < 12:
        return "***"
    return f"{key[:7]}...{key[-4:]}"
