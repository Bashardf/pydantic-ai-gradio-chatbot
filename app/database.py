from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel, Session, create_engine, select

from app.config import STORAGE_DIR

DB_FILE = STORAGE_DIR / "chatbot.db"
sqlite_url = f"sqlite:///{DB_FILE}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(index=True)
    client_id: str = Field(index=True)
    name: str
    phone: str
    city: str
    service: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str = Field(index=True, foreign_key="conversation.id")
    role: str
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sources: Optional[list] = Field(default=None, sa_column=Column(JSON))

    conversation: Optional["Conversation"] = Relationship(back_populates="messages")


class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True)
    client_id: str = Field(index=True)
    user_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    messages: List["Message"] = Relationship(back_populates="conversation")


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
