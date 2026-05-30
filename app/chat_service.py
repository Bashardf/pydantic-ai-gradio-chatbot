"""Gemeinsame Chat-Logik für FastAPI und Gradio."""

from __future__ import annotations

import shutil
import uuid
import logging
from pathlib import Path
from typing import AsyncIterator

from app import history, rag
from app.agent import AgentDeps, build_prompt, format_error, run_agent, run_agent_stream
from app.config import MODEL_NAME, UPLOADS_DIR
from app.schemas import ChatRequest, ChatResponse, SourceItem, UploadResponse, UsageInfo
from app.security.rate_limit import RateLimitExceeded, rate_limiter
from app.security.validation import (
    ValidationError,
    validate_chat_message,
    validate_client_id,
    validate_conversation_id,
    validate_pdf_upload,
    validate_user_id,
)

logger = logging.getLogger(__name__)


def _rate_key(client_id: str, user_id: str | None, ip: str | None) -> str:
    return f"{client_id}:{user_id or ip or 'anon'}"


def _hits_to_sources(hits) -> list[SourceItem]:
    return [
        SourceItem(
            file_name=h.file_name,
            file_id=h.file_id,
            page=h.page,
            score=round(h.score, 3),
            excerpt=h.excerpt,
        )
        for h in hits
    ]


def handle_chat(
    request: ChatRequest,
    rate_key: str | None = None,
) -> ChatResponse:
    message = validate_chat_message(request.message)
    client_id = validate_client_id(request.client_id)
    conversation_id = validate_conversation_id(request.conversation_id)
    user_id = validate_user_id(request.user_id)
    key = rate_key or _rate_key(client_id, user_id, None)

    rate_limiter.check("chat", key)

    prior = history.history_to_prompt_messages(client_id, conversation_id)
    sources: list[SourceItem] = []
    rag_context: str | None = None
    rag_required = False

    if request.use_rag:
        hits = rag.search(message, client_id=client_id)
        sources = _hits_to_sources(hits)
        if hits:
            rag_context = rag.hits_to_context(hits)
        else:
            rag_required = True

    prompt = build_prompt(message, prior, rag_context=rag_context, rag_required=rag_required)
    deps = AgentDeps(client_id=client_id, conversation_id=conversation_id)

    try:
        answer = run_agent(prompt, deps=deps)
    except Exception as exc:
        answer = format_error(exc)

    history.append_message(client_id, conversation_id, "user", message, user_id=user_id)
    history.append_message(
        client_id, conversation_id, "assistant", answer, sources=sources
    )

    return ChatResponse(
        answer=answer,
        conversation_id=conversation_id,
        sources=sources,
        usage=UsageInfo(model=MODEL_NAME),
    )


async def stream_chat(
    request: ChatRequest,
    rate_key: str | None = None,
) -> AsyncIterator[str | ChatResponse]:
    message = validate_chat_message(request.message)
    client_id = validate_client_id(request.client_id)
    conversation_id = validate_conversation_id(request.conversation_id)
    user_id = validate_user_id(request.user_id)
    key = rate_key or _rate_key(client_id, user_id, None)

    rate_limiter.check("chat", key)

    prior = history.history_to_prompt_messages(client_id, conversation_id)
    sources: list[SourceItem] = []
    rag_context: str | None = None
    rag_required = False

    if request.use_rag:
        hits = rag.search(message, client_id=client_id)
        sources = _hits_to_sources(hits)
        if hits:
            rag_context = rag.hits_to_context(hits)
        else:
            rag_required = True

    prompt = build_prompt(message, prior, rag_context=rag_context, rag_required=rag_required)
    deps = AgentDeps(client_id=client_id, conversation_id=conversation_id)

    history.append_message(client_id, conversation_id, "user", message, user_id=user_id)

    full_answer = ""
    try:
        async for chunk in run_agent_stream(prompt, deps=deps):
            full_answer = chunk
            yield chunk
    except Exception as exc:
        full_answer = format_error(exc)
        yield full_answer

    history.append_message(
        client_id, conversation_id, "assistant", full_answer, sources=sources
    )
    yield ChatResponse(
        answer=full_answer,
        conversation_id=conversation_id,
        sources=sources,
        usage=UsageInfo(model=MODEL_NAME),
    )


def process_upload_task(file_path: Path, client_id: str, file_id: str):
    """Hintergrund-Task zum Indexieren der PDF."""
    try:
        fid, name, count = rag.ingest_pdf(file_path, client_id=client_id, file_id=file_id)
        logger.info(f"Successfully indexed {count} chunks from {name} (ID: {fid})")
    except Exception as exc:
        logger.error(f"Failed to index {file_path}: {exc}")


def handle_upload_sync(
    file_path: Path,
    client_id: str = "default",
    rate_key: str | None = None,
) -> UploadResponse:
    """Synchrones Upload-Handling (für Gradio oder Tests)."""
    client_id = validate_client_id(client_id)
    key = rate_key or client_id
    rate_limiter.check("pdf_ingest", key)

    src, safe_name = validate_pdf_upload(file_path)
    file_id = str(uuid.uuid4())
    dest = UPLOADS_DIR / client_id / f"{file_id}_{safe_name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)

    fid, name, count = rag.ingest_pdf(dest, client_id=client_id, file_id=file_id)
    return UploadResponse(
        file_id=fid,
        file_name=name,
        status="indexed",
        message=f"Indexed {count} chunks from {name}.",
    )


def prepare_upload(
    file_path: Path,
    client_id: str = "default",
    rate_key: str | None = None,
) -> tuple[Path, str, str, str]:
    """Bereitet den Upload vor (Validierung + Verschieben), ohne zu indexieren."""
    client_id = validate_client_id(client_id)
    key = rate_key or client_id
    rate_limiter.check("pdf_ingest", key)

    src, safe_name = validate_pdf_upload(file_path)
    file_id = str(uuid.uuid4())
    dest = UPLOADS_DIR / client_id / f"{file_id}_{safe_name}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dest)
    
    return dest, client_id, file_id, safe_name
