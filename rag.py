"""Einfaches RAG: PDFs einlesen, embedden und durchsuchen."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from openai import OpenAI
from pypdf import PdfReader

from config import EMBEDDING_MODEL, RAG_DIR
from security.rate_limit import RateLimitExceeded, rate_limiter
from security.validation import MAX_PDF_PAGES, ValidationError, validate_search_query

INDEX_FILE = RAG_DIR / "index.json"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# Key nur aus Umgebungsvariable – nie im Code hardcoden
_client = OpenAI()


def _chunk_text(text: str) -> list[str]:
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


def _embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = _client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def _load_index() -> list[dict]:
    if not INDEX_FILE.exists():
        return []
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def _save_index(entries: list[dict]) -> None:
    INDEX_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ingest_pdf(pdf_path: Path) -> str:
    """Liest eine PDF, erstellt Chunks und speichert Embeddings."""
    rate_limiter.check("pdf_ingest")

    reader = PdfReader(str(pdf_path))
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValidationError(f"PDF hat zu viele Seiten (max. {MAX_PDF_PAGES}).")

    pages = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages).strip()
    if not full_text:
        return f"Kein Text in '{pdf_path.name}' gefunden."

    chunks = _chunk_text(full_text)
    if not chunks:
        return f"Keine verwertbaren Textabschnitte in '{pdf_path.name}'."

    embeddings = _embed(chunks)
    index = _load_index()
    source = pdf_path.name
    index = [entry for entry in index if entry.get("source") != source]

    for chunk, embedding in zip(chunks, embeddings):
        index.append({"source": source, "text": chunk, "embedding": embedding})

    _save_index(index)
    return f"'{source}' indexiert ({len(chunks)} Abschnitte)."


def search(query: str, top_k: int = 4) -> str:
    """Sucht relevante PDF-Abschnitte per Embedding-Ähnlichkeit."""
    try:
        rate_limiter.check("pdf_search")
    except RateLimitExceeded as exc:
        return str(exc)

    query = validate_search_query(query)
    index = _load_index()
    if not index:
        return "Noch keine PDFs indexiert. Lade zuerst eine PDF hoch."

    query_embedding = _embed([query])[0]
    query_vec = np.array(query_embedding)

    scored: list[tuple[float, dict]] = []
    for entry in index:
        vec = np.array(entry["embedding"])
        score = float(
            np.dot(query_vec, vec)
            / (np.linalg.norm(query_vec) * np.linalg.norm(vec) + 1e-9)
        )
        scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[:top_k]
    if not top or top[0][0] < 0.2:
        return "Keine passenden Passagen in den PDFs gefunden."

    parts = []
    for score, entry in top:
        parts.append(f"[{entry['source']} | Relevanz {score:.2f}]\n{entry['text']}")
    return "\n\n---\n\n".join(parts)


def list_sources() -> str:
    index = _load_index()
    if not index:
        return "Keine PDFs indexiert."
    sources = sorted({entry["source"] for entry in index})
    return "Indexierte PDFs:\n" + "\n".join(f"- {name}" for name in sources)
