"""Konfiguration: lädt Umgebungsvariablen aus .env und validiert sie."""

import os
from pathlib import Path

from dotenv import load_dotenv

from security.validation import validate_session_id

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAG_DIR = DATA_DIR / "rag"
HISTORY_DIR = DATA_DIR / "history"
PDF_UPLOAD_DIR = DATA_DIR / "pdfs"

# .env laden – Keys nur über os.environ, nicht als Modul-Konstante exportieren
load_dotenv(BASE_DIR / ".env", override=True)

_PLACEHOLDER_KEYS = {
    "your_openai_api_key_here",
    "sk-your-key-here",
    "sk-...",
}

_api_key = os.getenv("OPENAI_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "openai:gpt-4o-mini").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()

GRADIO_SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
GRADIO_SHARE = os.getenv("GRADIO_SHARE", "false").lower() in ("1", "true", "yes")
CHAT_SESSION_ID = validate_session_id(os.getenv("CHAT_SESSION_ID", "default"))

RATE_LIMIT_CHAT_REQUESTS = int(os.getenv("RATE_LIMIT_CHAT_REQUESTS", "30"))
RATE_LIMIT_CHAT_WINDOW = int(os.getenv("RATE_LIMIT_CHAT_WINDOW", "60"))
RATE_LIMIT_PDF_REQUESTS = int(os.getenv("RATE_LIMIT_PDF_REQUESTS", "5"))
RATE_LIMIT_PDF_WINDOW = int(os.getenv("RATE_LIMIT_PDF_WINDOW", "3600"))


def ensure_openai_api_key() -> None:
    """Prüft API-Key ohne ihn im Code zu speichern oder zu loggen."""
    if not _api_key:
        raise ValueError(
            "OPENAI_API_KEY fehlt. Lege .env an (siehe .env.example) "
            "und trage deinen Key ein."
        )
    if _api_key in _PLACEHOLDER_KEYS or _api_key.startswith("your_"):
        raise ValueError(
            "OPENAI_API_KEY ist noch der Platzhalter. "
            "https://platform.openai.com/account/api-keys"
        )
    if not _api_key.startswith("sk-"):
        raise ValueError("OPENAI_API_KEY sieht ungültig aus (erwartet: sk-...).")


ensure_openai_api_key()

for directory in (DATA_DIR, RAG_DIR, HISTORY_DIR, PDF_UPLOAD_DIR):
    directory.mkdir(parents=True, exist_ok=True)
