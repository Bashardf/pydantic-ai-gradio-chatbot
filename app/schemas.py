"""API Request/Response Modelle."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None
    user_id: str | None = None
    client_id: str = "default"
    use_rag: bool = True


class SourceItem(BaseModel):
    file_name: str
    file_id: str | None = None
    page: int | None = None
    score: float | None = None
    excerpt: str | None = None


class UsageInfo(BaseModel):
    model: str


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    sources: list[SourceItem] = Field(default_factory=list)
    usage: UsageInfo


class UploadResponse(BaseModel):
    file_id: str
    file_name: str
    status: str
    message: str


class HealthResponse(BaseModel):
    status: str
    model: str
    openai_configured: bool
    environment: str


class MessageRecord(BaseModel):
    role: str
    content: str
    timestamp: datetime
    sources: list[SourceItem] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    conversation_id: str
    client_id: str
    user_id: str | None = None
    messages: list[MessageRecord]
    lead: dict[str, Any] | None = None
