"""
Audio upload API route.
POST /api/v1/audio/upload — accepts audio files, validates, stores, returns metadata.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from app.audio.preprocessing import save_upload
from app.audio.validation import validate_upload
from app.schemas.schemas import AudioUploadResponse, ErrorResponse
from fastapi import APIRouter, File, UploadFile

router = APIRouter(prefix="/audio", tags=["Audio"])


@router.post(
    "/upload",
    response_model=AudioUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation failure"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
    summary="Upload an audio file for analysis",
    description="Accepts .wav, .mp3, .m4a, .flac files up to 50MB. "
    "Validates format, size, and duration before storing.",
)
async def upload_audio(file: Annotated[UploadFile, File(...)]):
    """
    Upload and validate a driver radio audio file.
    The file is stored safely and metadata is returned for subsequent analysis.
    """
    data, meta = await validate_upload(file)

    # Save to uploads directory
    file_id, storage_path = save_upload(data, file.filename or "unknown.wav")

    ext = Path(file.filename or "").suffix.lower()

    return AudioUploadResponse(
        file_id=file_id,
        filename=file.filename or "unknown",
        file_size_bytes=meta.file_size_bytes,
        duration_seconds=meta.duration_seconds if meta.duration_seconds > 0 else None,
        sample_rate=meta.sample_rate if meta.sample_rate > 0 else None,
        format=ext.lstrip("."),
        storage_path=f"data/uploads/{storage_path.name}",
    )
