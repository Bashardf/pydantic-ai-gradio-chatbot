"""Modulares RAG: PDF → Chunks → ChromaDB (Vektordatenbank)."""

from __future__ import annotations

import re
import uuid
import os
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from app.config import EMBEDDING_MODEL, RAG_DIR, _api_key
from app.security.rate_limit import RateLimitExceeded, rate_limiter
from app.security.validation import MAX_PDF_PAGES, ValidationError, validate_search_query

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
MIN_SCORE = 0.2

# ChromaDB Setup
chroma_client = chromadb.PersistentClient(path=str(RAG_DIR / "chroma_db"))

# Embedding Funktion sicher initialisieren
try:
    if _api_key and not _api_key.startswith("sk-proj-INVALID"):
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=_api_key,
            model_name=EMBEDDING_MODEL
        )
    else:
        openai_ef = None
except Exception:
    openai_ef = None

# Collection
collection = chroma_client.get_or_create_collection(
    name="documents",
    embedding_function=openai_ef,
    metadata={"hnsw:space": "cosine"}
)


@dataclass
class RagHit:
    file_name: str
    file_id: str
    page: int | None
    score: float
    excerpt: str


def _chunk_page_text(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def ingest_pdf(
    pdf_path: Path,
    client_id: str = "default",
    file_id: str | None = None,
) -> tuple[str, str, int]:
    """Indexiert PDF in ChromaDB."""
    if openai_ef is None:
        raise ValidationError("RAG ist deaktiviert, da kein gültiger OpenAI Key konfiguriert ist.")

    rate_limiter.check("pdf_ingest", client_id)

    reader = PdfReader(str(pdf_path))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValidationError(f"PDF hat zu viele Seiten (max. {MAX_PDF_PAGES}).")

    fid = file_id or str(uuid.uuid4())
    source = pdf_path.name

    collection.delete(where={"file_id": fid})

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for i, chunk in enumerate(_chunk_page_text(page_text)):
            documents.append(chunk)
            metadatas.append({
                "file_id": fid,
                "source": source,
                "client_id": client_id,
                "page": page_num
            })
            ids.append(f"{fid}_{page_num}_{i}")

    if not documents:
        raise ValidationError(f"Kein Text in '{source}' gefunden.")

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    return fid, source, len(documents)


def search(
    query: str,
    client_id: str = "default",
    top_k: int = 4,
) -> list[RagHit]:
    if openai_ef is None:
        return []

    try:
        rate_limiter.check("pdf_search", client_id)
    except RateLimitExceeded:
        raise

    query = validate_search_query(query)
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"client_id": client_id}
    )

    hits: list[RagHit] = []
    if not results or not results["documents"] or not results["documents"][0]:
        return []

    for i in range(len(results["documents"][0])):
        dist = results["distances"][0][i]
        score = 1.0 - dist
        
        if score < MIN_SCORE:
            continue
            
        metadata = results["metadatas"][0][i]
        hits.append(
            RagHit(
                file_name=metadata["source"],
                file_id=metadata["file_id"],
                page=metadata.get("page"),
                score=score,
                excerpt=results["documents"][0][i][:500],
            )
        )
    return hits


def hits_to_context(hits: list[RagHit]) -> str:
    if not hits:
        return ""
    parts = []
    for h in hits:
        page = f", page {h.page}" if h.page else ""
        parts.append(f"[{h.file_name}{page}]\n{h.excerpt}")
    return "\n\n---\n\n".join(parts)


def list_sources(client_id: str = "default") -> str:
    # Falls EF None ist, können wir get() trotzdem versuchen, falls bereits Daten da sind
    try:
        results = collection.get(where={"client_id": client_id}, include=["metadatas"])
        if not results or not results["metadatas"]:
            return "Keine PDFs indexiert."
        
        seen = {m["file_id"]: m["source"] for m in results["metadatas"]}
        return "Indexierte PDFs:\n" + "\n".join(f"- {name}" for name in sorted(seen.values()))
    except Exception:
        return "RAG Dienst momentan nicht verfügbar."
