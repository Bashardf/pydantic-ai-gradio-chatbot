"""Gradio Demo / Admin UI – nutzt dieselbe chat_service-Logik wie die API."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from app import history, rag
from app.chat_service import handle_chat, handle_upload_sync, stream_chat
from app.config import GRADIO_PORT, GRADIO_SHARE
from app.schemas import ChatRequest, ChatResponse

GRADIO_CLIENT_ID = "gradio-demo"
GRADIO_CONVERSATION_ID = "gradio-session"


def _load_chatbot_ui() -> list[dict[str, str]]:
    conv = history.get_conversation(GRADIO_CLIENT_ID, GRADIO_CONVERSATION_ID)
    return [{"role": m.role, "content": m.content} for m in conv.messages]


def _chat_sync(message: str, chatbot: list[dict]) -> tuple[str, list[dict]]:
    if not message.strip():
        return "", chatbot
    req = ChatRequest(
        message=message,
        conversation_id=GRADIO_CONVERSATION_ID,
        client_id=GRADIO_CLIENT_ID,
        use_rag=True,
    )
    resp = handle_chat(req, rate_key="gradio")
    chatbot = [
        *chatbot,
        {"role": "user", "content": message},
        {"role": "assistant", "content": resp.answer},
    ]
    return "", chatbot


async def _chat_stream(message: str, chatbot: list[dict]):
    if not message.strip():
        yield "", chatbot
        return
    req = ChatRequest(
        message=message,
        conversation_id=GRADIO_CONVERSATION_ID,
        client_id=GRADIO_CLIENT_ID,
        use_rag=True,
    )
    chatbot = [
        *chatbot,
        {"role": "user", "content": message},
        {"role": "assistant", "content": ""},
    ]
    yield "", chatbot

    async for chunk in stream_chat(req, rate_key="gradio"):
        if isinstance(chunk, ChatResponse):
            chatbot[-1]["content"] = chunk.answer
            yield "", chatbot
            return
        chatbot[-1]["content"] = chunk
        yield "", chatbot


def _ingest_pdf(file: str | None) -> str:
    if not file:
        return "Bitte PDF wählen."
    try:
        resp = handle_upload_sync(Path(file), client_id=GRADIO_CLIENT_ID, rate_key="gradio")
        return resp.message
    except Exception as exc:
        return str(exc)


def _clear() -> tuple[list, str]:
    history.clear_conversation(GRADIO_CLIENT_ID, GRADIO_CONVERSATION_ID)
    return [], "Verlauf gelöscht."


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Chatbot Demo (Gradio)") as demo:
        gr.Markdown(
            "# Gradio Demo UI\n"
            "Admin- und Test-Oberfläche. Produktions-Frontends nutzen **FastAPI** (Port 8000)."
        )
        status = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Chat", value=_load_chatbot_ui(), height=480)
                msg = gr.Textbox(placeholder="Nachricht …", show_label=False)
                with gr.Row():
                    stream_btn = gr.Button("Senden (Stream)", variant="primary")
                    sync_btn = gr.Button("Senden (sync)")
                    clear_btn = gr.Button("Löschen")
                stream_btn.click(_chat_stream, [msg, chatbot], [msg, chatbot])
                msg.submit(_chat_stream, [msg, chatbot], [msg, chatbot])
                sync_btn.click(_chat_sync, [msg, chatbot], [msg, chatbot])
                clear_btn.click(_clear, outputs=[chatbot, status])
            with gr.Column(scale=1):
                gr.Markdown("### PDF / RAG")
                pdf = gr.File(file_types=[".pdf"])
                ingest_btn = gr.Button("Indexieren")
                rag_status = gr.Textbox(label="RAG", interactive=False, lines=4)
                list_btn = gr.Button("PDFs anzeigen")
                ingest_btn.click(_ingest_pdf, pdf, rag_status)
                list_btn.click(lambda: rag.list_sources(GRADIO_CLIENT_ID), outputs=rag_status)
    return demo


if __name__ == "__main__":
    build_demo().queue().launch(server_name="0.0.0.0", server_port=GRADIO_PORT, share=GRADIO_SHARE)
