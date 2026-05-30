"""Eingabevalidierung."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import MAX_UPLOAD_BYTES

MAX_MESSAGE_LENGTH = 4_000
MAX_CALCULATOR_LENGTH = 120
MAX_SEARCH_QUERY_LENGTH = 500
MAX_TIMEZONE_LENGTH = 64
MAX_PDF_PAGES = 200
MAX_FILENAME_LENGTH = 200
MAX_HISTORY_MESSAGES = 200

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_TIMEZONE_PATTERN = re.compile(r"^[A-Za-z0-9_+\-/]+$")
_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class ValidationError(ValueError):
    pass


def secure_filename(name: str) -> str:
    base = Path(name).name
    safe = re.sub(r"[^\w.\- ]", "_", base).strip("._ ")
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf" if safe else "upload.pdf"
    return safe[:MAX_FILENAME_LENGTH] or "upload.pdf"


def validate_chat_message(message: str) -> str:
    if message is None:
        raise ValidationError("Nachricht fehlt.")
    text = message.strip()
    if not text:
        raise ValidationError("Leere Nachricht ist nicht erlaubt.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValidationError(f"Nachricht zu lang (max. {MAX_MESSAGE_LENGTH} Zeichen).")
    if _CONTROL_CHARS.search(text):
        raise ValidationError("Nachricht enthält ungültige Steuerzeichen.")
    return text


def validate_client_id(client_id: str | None) -> str:
    cid = (client_id or "default").strip()
    if not _ID_PATTERN.fullmatch(cid):
        raise ValidationError("client_id ungültig.")
    return cid


def validate_conversation_id(conversation_id: str | None) -> str:
    if not conversation_id:
        return str(uuid.uuid4())
    cid = conversation_id.strip()
    if not _ID_PATTERN.fullmatch(cid):
        raise ValidationError("conversation_id ungültig.")
    return cid


def validate_user_id(user_id: str | None) -> str | None:
    if not user_id:
        return None
    uid = user_id.strip()
    if not _ID_PATTERN.fullmatch(uid):
        raise ValidationError("user_id ungültig.")
    return uid


def validate_calculator_expression(expression: str) -> str:
    expr = (expression or "").strip()
    if not expr or len(expr) > MAX_CALCULATOR_LENGTH:
        raise ValidationError("Ungültiger Rechenausdruck.")
    if not re.fullmatch(r"[\d\s+\-*/().]+", expr):
        raise ValidationError("Nur Zahlen und Operatoren erlaubt.")
    return expr


def validate_search_query(query: str) -> str:
    q = (query or "").strip()
    if not q or len(q) > MAX_SEARCH_QUERY_LENGTH:
        raise ValidationError("Ungültige Suchanfrage.")
    if _CONTROL_CHARS.search(q):
        raise ValidationError("Suchanfrage enthält ungültige Zeichen.")
    return q


def validate_timezone(timezone: str) -> str:
    tz = (timezone or "Europe/Berlin").strip()
    if len(tz) > MAX_TIMEZONE_LENGTH or not _TIMEZONE_PATTERN.fullmatch(tz):
        raise ValidationError("Ungültige Zeitzone.")
    return tz


def validate_pdf_upload(file_path: Path) -> tuple[Path, str]:
    if not file_path.exists():
        raise ValidationError("Datei nicht gefunden.")
    if file_path.suffix.lower() != ".pdf":
        raise ValidationError("Nur PDF-Dateien erlaubt.")
    size = file_path.stat().st_size
    if size == 0:
        raise ValidationError("PDF ist leer.")
    if size > MAX_UPLOAD_BYTES:
        raise ValidationError(f"PDF zu groß (max. {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")
    if not file_path.read_bytes()[:5].startswith(b"%PDF-"):
        raise ValidationError("Keine gültige PDF.")
    return file_path, secure_filename(file_path.name)
