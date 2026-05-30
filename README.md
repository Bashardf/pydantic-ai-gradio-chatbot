# Pydantic AI Chatbot Template

An AI chatbot backend and website widget starter built with **Python**, **Pydantic AI**, **FastAPI**, **Gradio**, and **OpenAI**.

This project provides a production-oriented foundation for building intelligent assistants that can be embedded into company websites, used as internal document experts, or served as a standalone chat API.

## 🚀 Overview

This template bridges the gap between a simple LLM script and a real-world application. It includes message persistence, RAG (Retrieval-Augmented Generation) for PDF documents, a lead capture system, and a ready-to-use web widget.

### Use Cases:
*   **Customer Support:** Add an AI assistant to your website that knows your product documentation.
*   **Document Expert:** Chat with your own PDFs (brochures, manuals, contracts).
*   **Lead Generation:** Automatically capture and store potential customer info during chat.
*   **AI Engineering Portfolio:** A clean, modular example of a modern AI agent architecture.

## ✨ Features

### Implemented
- [x] **FastAPI Backend:** Robust REST API with SSE (Server-Sent Events) streaming support.
- [x] **Pydantic AI Agent:** Type-safe agent logic with integrated tools (Calculator, Time, Lead Capture).
- [x] **Advanced RAG:** PDF document ingestion and semantic search using **ChromaDB**.
- [x] **Persistent Storage:** Chat history and lead data stored in **SQLite** via **SQLModel**.
- [x] **Hybrid Model Support:** Use **OpenAI** (cloud) or **Ollama** (local) seamlessly.
- [x] **Web Widget:** Embeddable JavaScript/CSS widget for easy website integration.
- [x] **Admin/Demo UI:** **Gradio** interface for testing agent logic and uploading documents.
- [x] **Security:** Input validation, rate limiting, and secret redaction in logs.

### Planned / Roadmap
- [ ] Authentication & User Management (OAuth2).
- [ ] Multi-tenant support (separate knowledge bases per client).
- [ ] Support for local embeddings (fully offline RAG).
- [ ] Admin dashboard for lead management and chat analytics.
- [ ] Support for more file types (DOCX, CSV, Web Crawling).

## 🛠 Tech Stack

*   **Logic:** Python 3.12, [Pydantic AI](https://github.com/pydantic/pydantic-ai)
*   **API:** FastAPI, Uvicorn
*   **Database:** SQLModel (SQLAlchemy + Pydantic), SQLite
*   **Vector DB:** ChromaDB
*   **LLMs:** OpenAI (GPT-4o), Ollama (Llama 3)
*   **Frontend:** Gradio, Vanilla JS/CSS (Widget)

## 📐 Architecture

```text
       Website / App / Widget
                  |
                  v
           FastAPI Backend (:8000)
                  |
        ┌─────────┴─────────┐
        ▼                   ▼
  Pydantic AI Agent    History & Leads
        |            (SQLite/SQLModel)
        ├─> Tools (Lead Capture, Search)
        ├─> Knowledge Base (ChromaDB + PDFs)
        └─> LLM (OpenAI or Ollama)
```

## 📋 Getting Started

### Prerequisites
*   Python 3.12+
*   OpenAI API Key (optional if using Ollama)
*   Ollama (optional, for local models)

### Setup
1.  **Clone the repo:**
    ```bash
    git clone https://github.com/your-username/pydantic-ai-chatbot.git
    cd pydantic-ai-chatbot
    ```

2.  **Create virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows
    ```

3.  **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your keys and preferred model
    ```

### Running the Application

**1. Start the API (Production Backend):**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*   **Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Widget Demo:** [http://localhost:8000/widget/demo.html](http://localhost:8000/widget/demo.html)

**2. Start the Gradio UI (Admin/Demo):**
```bash
python -m app.gradio_app
```
*   **URL:** [http://localhost:7860](http://localhost:7860)

## 📖 API Usage

### Chat Endpoint
```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "What services do you offer?", "client_id": "my-site", "use_rag": true}'
```

### PDF Upload (Indexing)
```bash
curl -X POST "http://localhost:8000/upload?client_id=my-site" \
     -F "file=@brochure.pdf"
```
*Indexing happens asynchronously in the background.*

## 🔒 Security

*   **Secrets:** Never commit your `.env` file. A `scripts/check_secrets.py` script is included and runs in CI.
*   **Validation:** All inputs are strictly validated via regex and length limits.
*   **Production:** Use a reverse proxy (like Nginx) with HTTPS and add authentication before deploying publicly.

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Built as a professional AI engineering starter to explore high-level agent frameworks and robust RAG architectures.
