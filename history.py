"""Chatverlauf persistent speichern und laden."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import CHAT_SESSION_ID, HISTORY_DIR
from security.validation import MAX_HISTORY_MESSAGES, validate_session_id

try:
    from pydantic_ai.messages import ModelMessagesTypeAdapter

    _adapter = ModelMessagesTypeAdapter
    _HAS_ADAPTER = True
except ImportError:
    _adapter = None
    _HAS_ADAPTER = False


def _history_path(session_id: str | None = None) -> Path:
    sid = validate_session_id(session_id or CHAT_SESSION_ID)
    return HISTORY_DIR / f"{sid}.json"


def save_messages(messages: list[Any], session_id: str | None = None) -> None:
    """Speichert Pydantic-AI-Nachrichten als JSON (begrenzte Tiefe)."""
    if len(messages) > MAX_HISTORY_MESSAGES:
        messages = messages[-MAX_HISTORY_MESSAGES:]
    path = _history_path(session_id)
    if _HAS_ADAPTER and _adapter is not None:
        payload = json.loads(_adapter.dump_json(messages))
    else:
        payload = messages
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_messages(session_id: str | None = None) -> list[Any]:
    """Lädt gespeicherten Nachrichtenverlauf."""
    path = _history_path(session_id)
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if _HAS_ADAPTER and _adapter is not None:
        return _adapter.validate_python(payload)
    return payload


def clear_messages(session_id: str | None = None) -> None:
    """Löscht den gespeicherten Verlauf."""
    path = _history_path(session_id)
    if path.exists():
        path.unlink()
