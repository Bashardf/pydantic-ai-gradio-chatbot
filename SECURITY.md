# Security Policy

## Unterstützte Versionen

| Version | Unterstützt |
|---------|-------------|
| main    | ✅          |

## Meldung von Schwachstellen

Bitte **keine** Security-Issues mit API-Keys oder `.env`-Inhalten öffentlich posten.

Stattdessen:

1. Issue ohne sensible Daten öffnen, oder
2. Privat per E-Mail an den Maintainer melden

## Implementierte Maßnahmen

- **Keine Secrets im Code** – nur `.env` / Umgebungsvariablen
- **Secret-Scan** in CI (`scripts/check_secrets.py`)
- **Input-Validierung** – Nachrichtenlänge, PDF-Magic-Bytes, sichere Dateinamen
- **Rate Limits** – Chat- und PDF-Anfragen pro Zeitfenster
- **Fehler-Redaction** – API-Keys werden aus Fehlermeldungen entfernt

## Empfehlungen für Deployment

- `.env` niemals ins Repository committen
- `GRADIO_SHARE=false` in Produktion, wenn kein öffentlicher Demo-Link nötig ist
- Reverse Proxy mit Auth (z. B. nginx + Basic Auth) vor Gradio
- OpenAI API-Key mit Usage-Limits und Billing-Alerts
