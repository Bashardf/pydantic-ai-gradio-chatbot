from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ChatResponse, UsageInfo

client = TestClient(app)


def test_chat_rejects_empty_message():
    response = client.post("/chat", json={"message": "   ", "client_id": "test"})
    assert response.status_code == 400


@patch("app.chat_service.run_agent", return_value="Hallo, wie kann ich helfen?")
def test_chat_returns_answer(mock_run):
    response = client.post(
        "/chat",
        json={"message": "Hallo", "client_id": "test", "use_rag": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Hallo, wie kann ich helfen?"
    assert data["conversation_id"]
    mock_run.assert_called_once()


def test_upload_rejects_non_pdf():
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"client_id": "test"},
    )
    assert response.status_code == 400
