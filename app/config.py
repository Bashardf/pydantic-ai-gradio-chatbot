"""Zentrale Konfiguration aus Umgebungsvariablen."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
BASE_DIR = APP_DIR.parent

STORAGE_DIR = APP_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
CONVERSATIONS_DIR = STORAGE_DIR / "conversations"
RAG_DIR = STORAGE_DIR / "rag"
RAG_INDEX_FILE = RAG_DIR / "index.json"

# Legacy Gradio session path (optional)
LEGACY_HISTORY_DIR = BASE_DIR / "data" / "history"

load_dotenv(BASE_DIR / ".env", override=True)

_PLACEHOLDER_KEYS = {
    "your_openai_api_key_here",
    "sk-your-key-here",
    "sk-...",
}

_api_key = os.getenv("OPENAI_API_KEY", "").strip()

APP_ENV = os.getenv("APP_ENV", "development").strip()
APP_HOST = os.getenv("APP_HOST", "0.0.0.0").strip()
APP_PORT = int(os.getenv("APP_PORT", "8000"))
GRADIO_PORT = int(os.getenv("GRADIO_PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
GRADIO_SHARE = os.getenv("GRADIO_SHARE", "false").lower() in ("1", "true", "yes")

MODEL_NAME = os.getenv("MODEL_NAME", "openai:gpt-4o-mini").strip()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small").strip()

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_PDF_PER_HOUR = int(os.getenv("RATE_LIMIT_PDF_REQUESTS", "5"))
RATE_LIMIT_PDF_WINDOW = int(os.getenv("RATE_LIMIT_PDF_WINDOW", "3600"))

DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant for a website. Answer clearly, politely, and concisely.
If company documents or uploaded files are provided, use them as the main source of truth.
If you do not know the answer or the information is not available in the provided context, say so honestly.
Do not invent prices, policies, or guarantees.

When the user shows clear buying intent (wants a quote, appointment, or contact), politely ask for:
name, phone number, city, and requested service. Use the capture_lead tool when they provide these details."""

SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT).strip() or DEFAULT_SYSTEM_PROMPT

WIDGET_API_BASE = os.getenv("WIDGET_API_BASE", "http://localhost:8000").rstrip("/")
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "*").split(",")
    if o.strip()
]


def is_openai_configured() -> bool:
    return bool(_api_key and _api_key not in _PLACEHOLDER_KEYS and not _api_key.startswith("your_"))


def ensure_openai_api_key() -> None:
    if not _api_key:
        raise ValueError(
            "OPENAI_API_KEY fehlt. Lege .env an (siehe .env.example)."
        )
    if _api_key in _PLACEHOLDER_KEYS or _api_key.startswith("your_"):
        raise ValueError("OPENAI_API_KEY ist noch ein Platzhalter.")
    if not _api_key.startswith("sk-"):
        raise ValueError("OPENAI_API_KEY sieht ungültig aus.")


def init_storage() -> None:
    for path in (STORAGE_DIR, UPLOADS_DIR, CONVERSATIONS_DIR, RAG_DIR):
        path.mkdir(parents=True, exist_ok=True)


# Nur in laufenden Apps (API/Gradio), nicht beim Test-Import ohne Key
if os.getenv("SKIP_CONFIG_VALIDATION") != "1":
    if not MODEL_NAME.startswith("ollama:"):
        ensure_openai_api_key()
    init_storage()
