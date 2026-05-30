# pydantic-ai-gradio-chatbot

[![CI](https://github.com/Bashardf/pydantic-ai-gradio-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/Bashardf/pydantic-ai-gradio-chatbot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12.10-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Pydantic AI](https://img.shields.io/badge/Pydantic-AI-agent-orange.svg)](https://ai.pydantic.dev/)
[![Gradio](https://img.shields.io/badge/Gradio-6.7+-yellow.svg)](https://gradio.app/)

Ein produktionsnaher **OpenAI-Chatbot** mit [Pydantic AI](https://ai.pydantic.dev/), [Gradio](https://gradio.app/) und Security-Basics.

![Chatbot Features](https://img.shields.io/badge/Streaming-yes-success)
![RAG](https://img.shields.io/badge/RAG-PDF-blue)
![Tools](https://img.shields.io/badge/Tools-time%20%7C%20calc%20%7C%20search-informational)
![Rate Limits](https://img.shields.io/badge/Rate%20Limits-enabled-critical)

---

## Features

| Feature | Beschreibung |
|---------|--------------|
| 💬 **Chat** | Multi-Turn mit gespeichertem Verlauf |
| ⚡ **Streaming** | Antworten in Echtzeit |
| 🛠️ **Tools** | Uhrzeit, Rechner, PDF-Suche |
| 📄 **RAG** | PDF hochladen & Fragen stellen |
| 🔒 **Security** | Input-Validierung, Secret-Redaction, Rate-Limits |
| 🐳 **Docker** | `docker compose up` |

## Schnellstart

```bash
git clone https://github.com/Bashardf/pydantic-ai-gradio-chatbot.git
cd pydantic-ai-gradio-chatbot

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# OPENAI_API_KEY in .env eintragen und speichern!

python app.py
```

→ Browser: **http://127.0.0.1:7860**

## Konfiguration

```env
OPENAI_API_KEY=sk-...
MODEL_NAME=openai:gpt-4o-mini

# Rate Limits (optional)
RATE_LIMIT_CHAT_REQUESTS=30
RATE_LIMIT_CHAT_WINDOW=60
RATE_LIMIT_PDF_REQUESTS=5
RATE_LIMIT_PDF_WINDOW=3600
```

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `MODEL_NAME` | `openai:gpt-4o-mini` | OpenAI-Modell |
| `GRADIO_SHARE` | `false` | Öffentlicher Gradio-Link |
| `RATE_LIMIT_CHAT_*` | 30 / 60s | Max. Chat-Anfragen |

> ⚠️ **Niemals** `.env` committen. Nur `.env.example` ins Repo.

## Security

| Maßnahme | Details |
|----------|---------|
| **Input validation** | Max. 4000 Zeichen, PDF-Magic-Bytes, sichere Dateinamen |
| **Exposed secrets** | Keys nur in `.env`, Redaction in Fehlern, CI Secret-Scan |
| **Rate limits** | Chat & PDF-Upload pro Zeitfenster |

Details: [SECURITY.md](SECURITY.md)

```bash
python scripts/check_secrets.py   # lokal vor dem Push
```

## Projektstruktur

```
pydantic-ai-gradio-chatbot/
├── app.py                 # Gradio UI
├── agent.py               # Pydantic-AI Agent + Tools
├── config.py              # Konfiguration
├── rag.py                 # PDF RAG
├── history.py             # Chat-Persistenz
├── security/              # Validierung, Rate-Limits, Redaction
├── scripts/check_secrets.py
├── .github/workflows/ci.yml
├── Dockerfile
└── docker-compose.yml
```

## Docker

```bash
docker compose up --build
```

## Deployment

| Methode | Befehl / Setting |
|---------|------------------|
| Lokal | `python app.py` |
| Öffentlicher Link | `GRADIO_SHARE=true` in `.env` |
| Docker | `docker compose up` |

Für Produktion: Reverse Proxy mit Authentifizierung vor Gradio.

## Screenshots

> Nach dem ersten Start Screenshots in `docs/screenshots/` legen und hier verlinken.

## Tech Stack

- Python 3.12.10
- [Pydantic AI](https://ai.pydantic.dev/)
- [Gradio](https://gradio.app/) ≥ 6.7
- OpenAI API

## Lizenz

[MIT](LICENSE) — frei für Lern- und Demo-Projekte.

---

**Repo-Name:** `pydantic-ai-gradio-chatbot` — klar, suchbar, beschreibt den Stack.
