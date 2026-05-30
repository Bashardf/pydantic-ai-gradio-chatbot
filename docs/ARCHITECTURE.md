# Architecture

This document describes the internal structure of the Pydantic AI Chatbot.

## Design Philosophy

The project is built on three main pillars:
1.  **Type Safety:** Using Pydantic AI and SQLModel to ensure data integrity across the stack.
2.  **Modularity:** Decoupling the AI logic (Agent), the API layer (FastAPI), and the storage/search layer (RAG/SQL).
3.  **Local-First Readiness:** Supporting both cloud (OpenAI) and local (Ollama) workflows out of the box.

## Core Components

### 1. Pydantic AI Agent (`app/agent.py`)
The "brain" of the system. It defines:
*   **System Prompts:** Instructions for the assistant.
*   **Tools:** Python functions the LLM can call (Lead Capture, Search, etc.).
*   **Dependencies:** Context injected into tools (like `client_id`).

### 2. FastAPI Backend (`app/main.py` & `app/api/`)
The communication layer. It handles:
*   **Streaming (SSE):** Real-time token-by-token delivery to the frontend.
*   **Asynchronicity:** Background tasks for heavy processing (PDF indexing).
*   **Validation:** Strict Pydantic schemas for all requests.

### 3. RAG Engine (`app/rag.py`)
The knowledge layer. It implements a semantic search pipeline:
*   **Preprocessing:** PDF text extraction and chunking with overlap.
*   **Vector Storage:** ChromaDB for storing and querying document embeddings.
*   **Retrieval:** Similarity search to inject context into the Agent's prompt.

### 4. Storage (`app/database.py` & `app/history.py`)
The memory layer. Uses SQLModel (SQLAlchemy) with SQLite:
*   **Conversations:** Persistent message history.
*   **Leads:** Structured storage for data captured by the agent.

## Data Flow

1.  **Request:** User sends a message via Widget or API.
2.  **Validation:** FastAPI validates the schema and checks rate limits.
3.  **RAG (Optional):** If RAG is enabled, the system queries ChromaDB for relevant document snippets.
4.  **Agent:** The Pydantic AI Agent is invoked with the message, history, and retrieved snippets.
5.  **Tools:** If the user shows buying intent, the Agent calls `capture_lead`.
6.  **Response:** The answer is streamed back via SSE and saved to the database.
