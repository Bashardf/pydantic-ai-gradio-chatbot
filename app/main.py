"""FastAPI entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.api.routes_chat import conversations_router, router as chat_router
from app.api.routes_files import router as files_router
from app.api.routes_health import router as health_router
from app.config import APP_ENV, CORS_ORIGINS
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Datenbank initialisieren
    init_db()
    yield


app = FastAPI(
    title="Pydantic AI Chatbot API",
    description="Production-ready chat API with RAG, streaming, and multi-client support.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(files_router)

_widget_dir = Path(__file__).parent / "widget"
if _widget_dir.exists():
    app.mount("/widget", StaticFiles(directory=_widget_dir), name="widget")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    """Browser request – avoids 404 noise in logs."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<circle cx="16" cy="16" r="14" fill="#2563eb"/>'
        "</svg>"
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/")
def root():
    return {
        "service": "pydantic-ai-gradio-chatbot",
        "docs": "/docs",
        "health": "/health",
        "widget": "/widget/demo.html",
        "environment": APP_ENV,
    }
