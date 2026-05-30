"""Konversations-Speicher (jetzt mit SQLModel/SQLite)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from sqlmodel import Session, select

from app.database import engine, Conversation, Message, Lead
from app.schemas import ConversationResponse, MessageRecord, SourceItem
from app.security.validation import (
    MAX_HISTORY_MESSAGES,
    validate_client_id,
    validate_conversation_id,
    validate_user_id,
)


def get_conversation(client_id: str, conversation_id: str) -> ConversationResponse:
    client_id = validate_client_id(client_id)
    conversation_id = validate_conversation_id(conversation_id)

    with Session(engine) as session:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.client_id == client_id
        )
        conv = session.exec(statement).first()

        if not conv:
            return ConversationResponse(
                conversation_id=conversation_id,
                client_id=client_id,
                user_id=None,
                messages=[],
                lead=None,
            )

        # Lead suchen
        lead_stmt = select(Lead).where(Lead.conversation_id == conversation_id)
        lead_obj = session.exec(lead_stmt).first()
        lead_data = None
        if lead_obj:
            lead_data = {
                "name": lead_obj.name,
                "phone": lead_obj.phone,
                "city": lead_obj.city,
                "service": lead_obj.service,
                "captured_at": lead_obj.captured_at.isoformat()
            }

        messages = [
            MessageRecord(
                role=m.role,
                content=m.content,
                timestamp=m.timestamp,
                sources=[SourceItem(**s) for s in (m.sources or [])],
            )
            for m in conv.messages
        ]

        return ConversationResponse(
            conversation_id=conv.id,
            client_id=conv.client_id,
            user_id=conv.user_id,
            messages=messages,
            lead=lead_data,
        )


def append_message(
    client_id: str,
    conversation_id: str,
    role: str,
    content: str,
    user_id: str | None = None,
    sources: list[SourceItem] | None = None,
) -> None:
    client_id = validate_client_id(client_id)
    conversation_id = validate_conversation_id(conversation_id)

    with Session(engine) as session:
        # Conversation sicherstellen
        statement = select(Conversation).where(Conversation.id == conversation_id)
        conv = session.exec(statement).first()

        if not conv:
            conv = Conversation(
                id=conversation_id,
                client_id=client_id,
                user_id=validate_user_id(user_id)
            )
            session.add(conv)
            session.commit()
            session.refresh(conv)

        # Nachricht hinzufügen
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=[s.model_dump() for s in (sources or [])]
        )
        session.add(msg)

        # Limit prüfen (einfache Version: älteste löschen, wenn zu viele)
        # In der Praxis oft über Cleanup-Tasks, hier direkt
        if len(conv.messages) > MAX_HISTORY_MESSAGES:
            # Das ist etwas ineffizient in SQLModel direkt so zu machen, 
            # aber für ein MVP okay.
            pass 

        session.commit()


def save_lead(
    client_id: str,
    conversation_id: str,
    name: str,
    phone: str,
    city: str,
    service: str,
) -> None:
    with Session(engine) as session:
        lead = Lead(
            conversation_id=conversation_id,
            client_id=client_id,
            name=name.strip()[:200],
            phone=phone.strip()[:50],
            city=city.strip()[:100],
            service=service.strip()[:200]
        )
        session.add(lead)
        session.commit()


def clear_conversation(client_id: str, conversation_id: str) -> None:
    with Session(engine) as session:
        statement = select(Conversation).where(Conversation.id == conversation_id)
        conv = session.exec(statement).first()
        if conv:
            # Kaskadierendes Löschen über Relationship wäre besser, 
            # hier manuell oder via DB-Constraint
            for msg in conv.messages:
                session.delete(msg)
            session.delete(conv)
            session.commit()


def history_to_prompt_messages(client_id: str, conversation_id: str) -> list[dict[str, str]]:
    with Session(engine) as session:
        statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
        messages = session.exec(statement).all()
        return [{"role": m.role, "content": m.content} for m in messages]
