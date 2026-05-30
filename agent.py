"""Pydantic-AI-Agent mit Tools, Streaming und Chatverlauf."""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from typing import Any, AsyncIterator
from zoneinfo import ZoneInfo

from pydantic_ai import Agent

import rag
from config import MODEL_NAME
from security.rate_limit import RateLimitExceeded, rate_limiter
from security.secrets import redact_secrets
from security.validation import (
    validate_calculator_expression,
    validate_search_query,
    validate_timezone,
)

SYSTEM_PROMPT = """Du bist ein hilfreicher, klarer und freundlicher Assistent.
Bei Programmierfragen erklärst du Schritt für Schritt.
Wenn du etwas nicht weißt, sagst du das ehrlich.

Du hast Tools:
- current_time: aktuelle Uhrzeit
- calculator: einfache Mathematik
- search_documents: durchsucht hochgeladene PDFs (RAG)
- list_documents: zeigt indexierte PDFs

Nutze search_documents, wenn der Nutzer Fragen zu hochgeladenen Dokumenten stellt."""

agent = Agent(MODEL_NAME, instructions=SYSTEM_PROMPT)

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    raise ValueError("Nur einfache Rechenausdrücke erlaubt")


@agent.tool_plain
async def current_time(timezone: str = "Europe/Berlin") -> str:
    """Gibt die aktuelle Uhrzeit in ISO-Format zurück."""
    tz_name = validate_timezone(timezone)
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz=tz).isoformat()


@agent.tool_plain
async def calculator(expression: str) -> str:
    """Berechnet einen mathematischen Ausdruck, z. B. (2 + 3) * 4."""
    try:
        expr = validate_calculator_expression(expression)
        tree = ast.parse(expr, mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except Exception as exc:
        return f"Berechnung fehlgeschlagen: {exc}"


@agent.tool_plain
async def search_documents(query: str) -> str:
    """Durchsucht hochgeladene PDF-Dokumente nach relevanten Passagen."""
    return rag.search(validate_search_query(query))


@agent.tool_plain
async def list_documents() -> str:
    """Listet alle indexierten PDF-Dateien."""
    return rag.list_sources()


def format_error(exc: Exception) -> str:
    """Wandelt technische Fehler in verständliche, redigierte Hinweise um."""
    if isinstance(exc, RateLimitExceeded):
        return str(exc)

    message = redact_secrets(str(exc)).lower()
    raw = redact_secrets(str(exc))

    if "401" in message or "invalid_api_key" in message or "incorrect api key" in message:
        return (
            "Der OpenAI API-Key ist ungültig. Prüfe OPENAI_API_KEY in .env "
            "und starte die App neu."
        )
    if "404" in message or ("model" in message and "not found" in message):
        return (
            "Das Modell ist nicht verfügbar. Passe MODEL_NAME in .env an, "
            "z. B. openai:gpt-4o-mini"
        )
    if "429" in message or "insufficient_quota" in message or "quota" in message:
        return (
            "OpenAI-Guthaben oder Limit erreicht. "
            "https://platform.openai.com/account/billing"
        )
    return f"Entschuldigung, es ist ein Fehler aufgetreten: {raw}"


def _guard_request(user_message: str) -> None:
    rate_limiter.check("chat")


def ask_agent(
    user_message: str, message_history: list[Any] | None = None
) -> tuple[str, list[Any]]:
    try:
        _guard_request(user_message)
        result = agent.run_sync(user_message, message_history=message_history or [])
        return result.output, result.all_messages()
    except Exception as exc:
        return format_error(exc), message_history or []


async def ask_agent_stream(
    user_message: str, message_history: list[Any] | None = None
) -> AsyncIterator[str | list[Any]]:
    try:
        _guard_request(user_message)
        async with agent.run_stream(
            user_message, message_history=message_history or []
        ) as result:
            async for text in result.stream_text():
                yield text
            yield result.all_messages()
    except Exception as exc:
        yield format_error(exc)
        yield message_history or []
