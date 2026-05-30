"""Eingabevalidierung für Chat, PDFs und Tool-Parameter."""

from __future__ import annotations

import re
from pathlib import Path

MAX_MESSAGE_LENGTH = 4_000
MAX_CALCULATOR_LENGTH = 120
MAX_SEARCH_QUERY_LENGTH = 500
MAX_TIMEZONE_LENGTH = 64
MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_PDF_PAGES = 200
MAX_FILENAME_LENGTH = 200
MAX_HISTORY_MESSAGES = 100

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_TIMEZONE_PATTERN = re.compile(r"^[A-Za-z0-9_+\-/]+$")
_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class ValidationError(ValueError):
    """Ungültige Benutzereingabe."""


def secure_filename(name: str) -> str:
    """Entfernt Pfadbestandteile und gefährliche Zeichen."""
    base = Path(name).name
    safe = re.sub(r"[^\w.\- ]", "_", base).strip("._ ")
    if not safe.lower().endswith(".pdf"):
        safe = f"{safe}.pdf" if safe else "upload.pdf"
    return safe[:MAX_FILENAME_LENGTH] or "upload.pdf"


def validate_chat_message(message: str) -> str:
    """Validiert und bereinigt Chat-Nachrichten."""
    if message is None:
        raise ValidationError("Nachricht fehlt.")
    text = message.strip()
    if not text:
        raise ValidationError("Leere Nachricht ist nicht erlaubt.")
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValidationError(
            f"Nachricht zu lang (max. {MAX_MESSAGE_LENGTH} Zeichen)."
        )
    if _CONTROL_CHARS.search(text):
        raise ValidationError("Nachricht enthält ungültige Steuerzeichen.")
    return text


def validate_calculator_expression(expression: str) -> str:
    """Validiert Rechner-Eingaben."""
    expr = (expression or "").strip()
    if not expr:
        raise ValidationError("Leerer Ausdruck.")
    if len(expr) > MAX_CALCULATOR_LENGTH:
        raise ValidationError("Ausdruck zu lang.")
    if not re.fullmatch(r"[\d\s+\-*/().]+", expr):
        raise ValidationError("Nur Zahlen und + - * / ( ) erlaubt.")
    return expr


def validate_search_query(query: str) -> str:
    """Validiert RAG-Suchanfragen."""
    q = (query or "").strip()
    if not q:
        raise ValidationError("Leere Suchanfrage.")
    if len(q) > MAX_SEARCH_QUERY_LENGTH:
        raise ValidationError("Suchanfrage zu lang.")
    if _CONTROL_CHARS.search(q):
        raise ValidationError("Suchanfrage enthält ungültige Zeichen.")
    return q


def validate_timezone(timezone: str) -> str:
    """Validiert Zeitzonen-Strings."""
    tz = (timezone or "Europe/Berlin").strip()
    if len(tz) > MAX_TIMEZONE_LENGTH:
        raise ValidationError("Zeitzonenname zu lang.")
    if not _TIMEZONE_PATTERN.fullmatch(tz):
        raise ValidationError("Ungültiger Zeitzonenname.")
    return tz


def validate_session_id(session_id: str) -> str:
    """Verhindert Path-Traversal in Session-Dateinamen."""
    sid = (session_id or "default").strip()
    if not _SESSION_ID_PATTERN.fullmatch(sid):
        raise ValidationError(
            "CHAT_SESSION_ID darf nur Buchstaben, Zahlen, _ und - enthalten."
        )
    return sid


def validate_pdf_upload(file_path: Path) -> tuple[Path, str]:
    """
    Validiert hochgeladene PDFs (Existenz, Größe, Magic Bytes).
    Gibt (Pfad, sicherer Dateiname) zurück.
    """
    if not file_path.exists():
        raise ValidationError("Datei nicht gefunden.")
    if file_path.suffix.lower() != ".pdf":
        raise ValidationError("Nur PDF-Dateien erlaubt.")

    size = file_path.stat().st_size
    if size == 0:
        raise ValidationError("PDF ist leer.")
    if size > MAX_PDF_BYTES:
        raise ValidationError(f"PDF zu groß (max. {MAX_PDF_BYTES // (1024 * 1024)} MB).")

    header = file_path.read_bytes()[:5]
    if not header.startswith(b"%PDF-"):
        raise ValidationError("Datei ist keine gültige PDF.")

    safe_name = secure_filename(file_path.name)
    return file_path, safe_name
