"""Gradio-Frontend mit Streaming, RAG, Tools, Verlauf und Sicherheits-Guards."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import gradio as gr

from agent import ask_agent, ask_agent_stream, format_error
from config import GRADIO_SERVER_PORT, GRADIO_SHARE, PDF_UPLOAD_DIR
from history import clear_messages, load_messages, save_messages
import rag
from security.rate_limit import RateLimitExceeded
from security.validation import (
    ValidationError,
    validate_chat_message,
    validate_pdf_upload,
)

_initial_messages: list[Any] = load_messages()


def _to_gradio_history(messages: list[Any]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for msg in messages:
        parts = getattr(msg, "parts", [])
        role = getattr(msg, "role", None)
        kind = getattr(msg, "kind", None)
        texts: list[str] = []
        for part in parts:
            content = getattr(part, "content", None)
            if isinstance(content, str) and content.strip():
                texts.append(content)
        if not texts:
            continue
        text = "\n".join(texts)
        if role == "user" or kind == "request":
            history.append({"role": "user", "content": text})
        elif role in ("assistant", "model") or kind == "response":
            history.append({"role": "assistant", "content": text})
    return history


def _handle_user_error(
    exc: Exception, chatbot: list[dict], past_messages: list[Any]
) -> tuple[str, list[dict], list[Any]]:
    """Zeigt Validierungs- und Rate-Limit-Fehler im Chat an."""
    if isinstance(exc, (ValidationError, RateLimitExceeded)):
        msg = str(exc)
    else:
        msg = format_error(exc)
    chatbot = [*chatbot, {"role": "assistant", "content": f"⚠️ {msg}"}]
    return "", chatbot, past_messages


async def stream_chat(
    message: str,
    chatbot: list[dict],
    past_messages: list[Any],
):
    try:
        message = validate_chat_message(message)
    except (ValidationError, RateLimitExceeded) as exc:
        yield _handle_user_error(exc, chatbot, past_messages)
        return

    chatbot = [*chatbot, {"role": "user", "content": message}, {"role": "assistant", "content": ""}]
    yield "", chatbot, past_messages

    new_messages = past_messages
    async for chunk in ask_agent_stream(message, past_messages):
        if isinstance(chunk, list):
            new_messages = chunk
            save_messages(new_messages)
            yield "", chatbot, new_messages
            return
        chatbot[-1]["content"] = chunk
        yield "", chatbot, past_messages


def chat_sync(message: str, chatbot: list[dict], past_messages: list[Any]):
    try:
        message = validate_chat_message(message)
    except (ValidationError, RateLimitExceeded) as exc:
        return _handle_user_error(exc, chatbot, past_messages)

    reply, new_messages = ask_agent(message, past_messages)
    chatbot = [
        *chatbot,
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    save_messages(new_messages)
    return "", chatbot, new_messages


def ingest_pdf_upload(file: str | None) -> str:
    if not file:
        return "Bitte eine PDF-Datei auswählen."
    try:
        src, safe_name = validate_pdf_upload(Path(file))
        dest = PDF_UPLOAD_DIR / safe_name
        shutil.copy(src, dest)
        return rag.ingest_pdf(dest)
    except (ValidationError, RateLimitExceeded) as exc:
        return str(exc)
    except Exception as exc:
        return format_error(exc)


def clear_chat() -> tuple[list, list, str]:
    clear_messages()
    return [], [], "Chatverlauf gelöscht."


with gr.Blocks(title="OpenAI Chatbot") as demo:
    gr.Markdown(
        "# Mein OpenAI Chatbot\n"
        "Streaming · Tools · RAG · persistenter Verlauf · Rate-Limits"
    )

    past_messages = gr.State(_initial_messages)

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Chat",
                value=_to_gradio_history(_initial_messages),
                height=480,
            )
            msg = gr.Textbox(
                label="Nachricht",
                placeholder="Stelle eine Frage … (max. 4000 Zeichen)",
                show_label=False,
                max_lines=10,
            )
            with gr.Row():
                send_stream = gr.Button("Senden (Stream)", variant="primary")
                send_sync = gr.Button("Senden (ohne Stream)")
                clear_btn = gr.Button("Verlauf löschen")
            gr.Examples(
                examples=[
                    "Erkläre mir Python-Listen Schritt für Schritt.",
                    "Was ist 17 * 23 + 5?",
                    "Wie spät ist es in Berlin?",
                    "Welche PDFs sind indexiert?",
                ],
                inputs=msg,
            )
            status = gr.Textbox(label="Status", interactive=False)

        with gr.Column(scale=1):
            gr.Markdown("### PDF-Wissen (RAG)\nMax. 10 MB · PDF only")
            pdf_upload = gr.File(label="PDF hochladen", file_types=[".pdf"])
            ingest_btn = gr.Button("PDF indexieren", variant="secondary")
            rag_status = gr.Textbox(label="RAG-Status", interactive=False, lines=4)
            refresh_pdfs = gr.Button("Indexierte PDFs anzeigen")

    send_stream.click(
        stream_chat,
        inputs=[msg, chatbot, past_messages],
        outputs=[msg, chatbot, past_messages],
    )
    msg.submit(
        stream_chat,
        inputs=[msg, chatbot, past_messages],
        outputs=[msg, chatbot, past_messages],
    )
    send_sync.click(
        chat_sync,
        inputs=[msg, chatbot, past_messages],
        outputs=[msg, chatbot, past_messages],
    )

    ingest_btn.click(ingest_pdf_upload, inputs=pdf_upload, outputs=rag_status)
    refresh_pdfs.click(rag.list_sources, outputs=rag_status)
    clear_btn.click(clear_chat, outputs=[chatbot, past_messages, status])

if __name__ == "__main__":
    demo.queue().launch(
        server_port=GRADIO_SERVER_PORT,
        share=GRADIO_SHARE,
    )
