# Security Policy

This project takes security seriously. Below are the measures implemented to ensure a safe and professional deployment.

## 1. Secret Management
*   **No Hardcoded Keys:** All API keys (OpenAI, etc.) are loaded via environment variables (`.env`).
*   **Redaction:** The `app/security/secrets.py` module automatically redacts API keys and sensitive patterns from error messages and logs before they reach the frontend.
*   **CI Scanning:** A `check_secrets.py` script runs in GitHub Actions to prevent accidental commits of sensitive data.

## 2. Input Validation
*   **Strict Schemas:** Every API endpoint uses Pydantic models for request validation.
*   **Regex Checks:** Client IDs, Conversation IDs, and user inputs are filtered for illegal characters (control characters, long strings) to prevent injection attacks.
*   **PDF Sanitization:** Uploaded files are checked for magic bytes (`%PDF-`), size limits, and filenames are sanitized.

## 3. Rate Limiting
*   **Multi-Level Limits:** Rate limits are applied per IP and per `client_id` for chat requests and PDF uploads to prevent resource exhaustion and API cost spikes.
*   **Configurable:** All limits can be tuned via the `.env` file.

## 4. RAG & Prompt Protection
*   **Context Isolation:** Document excerpts retrieved via RAG are placed in a restricted XML-like block (`<retrieved_documents>`) with instructions for the LLM to ignore any commands within those excerpts.
*   **Calculators:** The integrated calculator tool uses `ast.parse` and a restricted set of allowed operators instead of `eval()` to prevent remote code execution (RCE).

## 5. Deployment Recommendations
*   **Authentication:** The current version is a template and does **not** include an authentication layer (OAuth2/JWT) by default. Add an auth layer (e.g., FastAPI Users) before public deployment.
*   **HTTPS:** Always run behind a reverse proxy (Nginx, Traefik) with SSL/TLS.
*   **Database:** For high-traffic applications, migrate from SQLite to a dedicated PostgreSQL instance.
