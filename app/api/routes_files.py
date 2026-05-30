from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, BackgroundTasks

from app.chat_service import prepare_upload, process_upload_task
from app.schemas import UploadResponse
from app.security.rate_limit import RateLimitExceeded
from app.security.validation import ValidationError, validate_client_id

router = APIRouter(prefix="/upload", tags=["files"])


@router.post("", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    client_id: str = "default",
) -> UploadResponse:
    client_id = validate_client_id(client_id)
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # Temporäre Datei zum Zwischenspeichern
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        ip = request.client.host if request.client else "unknown"
        # 1. Validieren und an endgültigen Ort verschieben
        dest_path, cid, fid, name = prepare_upload(
            tmp_path, client_id=client_id, rate_key=f"{client_id}:{ip}"
        )
        
        # 2. Indexierung im Hintergrund starten
        background_tasks.add_task(process_upload_task, dest_path, cid, fid)
        
        return UploadResponse(
            file_id=fid,
            file_name=name,
            status="processing",
            message=f"File {name} uploaded and is being processed in the background.",
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        # Die temporäre Datei löschen (die Kopie in UPLOADS_DIR bleibt)
        tmp_path.unlink(missing_ok=True)
