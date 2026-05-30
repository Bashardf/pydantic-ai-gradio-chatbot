from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app import history
from app.chat_service import handle_chat, stream_chat
from app.schemas import ChatRequest, ChatResponse, ConversationResponse
from app.security.rate_limit import RateLimitExceeded
from app.security.validation import ValidationError, validate_client_id, validate_conversation_id

router = APIRouter(prefix="/chat", tags=["chat"])


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


@router.post("", response_model=ChatResponse)
def chat(request_body: ChatRequest, request: Request) -> ChatResponse:
    rate_key = f"{request_body.client_id}:{request_body.user_id or _client_ip(request)}"
    try:
        return handle_chat(request_body, rate_key=rate_key)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.post("/stream")
async def chat_stream_endpoint(request_body: ChatRequest, request: Request):
    rate_key = f"{request_body.client_id}:{request_body.user_id or _client_ip(request)}"

    async def event_generator():
        try:
            async for chunk in stream_chat(request_body, rate_key=rate_key):
                if isinstance(chunk, ChatResponse):
                    payload = {
                        "event": "done",
                        "conversation_id": chunk.conversation_id,
                        "sources": [s.model_dump() for s in chunk.sources],
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    yield f"data: {json.dumps({'event': 'token', 'text': chunk})}\n\n"
        except (ValidationError, RateLimitExceeded) as exc:
            yield f"data: {json.dumps({'event': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


conversations_router = APIRouter(tags=["conversations"])


@conversations_router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    client_id: str = "default",
) -> ConversationResponse:
    return history.get_conversation(
        validate_client_id(client_id),
        validate_conversation_id(conversation_id),
    )
