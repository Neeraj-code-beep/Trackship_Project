"""
Audio file validation module.
Handles format, size, duration, and sample rate validation.
"""

from __future__ import annotations

import io
import struct
import wave
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException

from backend.app.core.config import settings


class AudioValidationError(Exception):
    """Raised when audio validation fails."""

    def __init__(self, message: str, error_code: str = "AUDIO_VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AudioMetadata:
    """Container for extracted audio file metadata."""

    def __init__(
        self,
        duration_seconds: float = 0.0,
        sample_rate: int = 0,
        channels: int = 0,
        bit_depth: int = 0,
        file_size_bytes: int = 0,
        format_ext: str = "",
    ):
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        self.bit_depth = bit_depth
        self.file_size_bytes = file_size_bytes
        self.format_ext = format_ext


def validate_extension(filename: str) -> str:
    """Validate file extension is in allowed list. Returns normalized extension."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}",
            error_code="UNSUPPORTED_FORMAT",
        )
    return ext


def validate_content_type(content_type: Optional[str]) -> None:
    """Validate MIME type if provided."""
    if content_type and content_type not in settings.ALLOWED_MIME_TYPES:
        # Be permissive: some clients send generic types
        if not content_type.startswith("audio/") and content_type != "application/octet-stream":
            raise AudioValidationError(
                f"Invalid content type '{content_type}'. Expected an audio MIME type.",
                error_code="INVALID_CONTENT_TYPE",
            )


def validate_file_size(size_bytes: int) -> None:
    """Ensure file size is within acceptable limits."""
    if size_bytes <= 0:
        raise AudioValidationError(
            "File is empty.",
            error_code="EMPTY_FILE",
        )
    if size_bytes > settings.MAX_AUDIO_SIZE_BYTES:
        max_mb = settings.MAX_AUDIO_SIZE_BYTES / (1024 * 1024)
        actual_mb = size_bytes / (1024 * 1024)
        raise AudioValidationError(
            f"File size {actual_mb:.1f}MB exceeds maximum {max_mb:.0f}MB.",
            error_code="FILE_TOO_LARGE",
        )


def _parse_wav_header(data: bytes) -> AudioMetadata:
    """Parse WAV header to extract metadata without external libraries."""
    try:
        buf = io.BytesIO(data)
        with wave.open(buf, "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            sample_width = wf.getsampwidth()
            duration = n_frames / sample_rate if sample_rate > 0 else 0.0
            return AudioMetadata(
                duration_seconds=duration,
                sample_rate=sample_rate,
                channels=channels,
                bit_depth=sample_width * 8,
                file_size_bytes=len(data),
                format_ext=".wav",
            )
    except Exception:
        return AudioMetadata(file_size_bytes=len(data), format_ext=".wav")


def _estimate_mp3_duration(data: bytes) -> AudioMetadata:
    """Rough estimate of MP3 duration from file size and assumed bitrate."""
    # Assume 128kbps average bitrate for estimation
    assumed_bitrate = 128_000  # bits per second
    size_bits = len(data) * 8
    duration = size_bits / assumed_bitrate if assumed_bitrate > 0 else 0.0
    return AudioMetadata(
        duration_seconds=duration,
        sample_rate=44100,  # common default
        channels=2,
        bit_depth=16,
        file_size_bytes=len(data),
        format_ext=".mp3",
    )


def extract_metadata(data: bytes, ext: str) -> AudioMetadata:
    """Extract audio metadata based on format. Falls back to size-based estimates."""
    if ext == ".wav":
        return _parse_wav_header(data)
    elif ext in (".mp3", ".m4a", ".flac"):
        return _estimate_mp3_duration(data)
    else:
        return AudioMetadata(file_size_bytes=len(data), format_ext=ext)


def validate_duration(meta: AudioMetadata) -> None:
    """Validate audio duration is within acceptable range."""
    if meta.duration_seconds > 0:
        if meta.duration_seconds < settings.MIN_DURATION_SECONDS:
            raise AudioValidationError(
                f"Audio too short ({meta.duration_seconds:.2f}s). "
                f"Minimum is {settings.MIN_DURATION_SECONDS}s.",
                error_code="AUDIO_TOO_SHORT",
            )
        if meta.duration_seconds > settings.MAX_DURATION_SECONDS:
            raise AudioValidationError(
                f"Audio too long ({meta.duration_seconds:.1f}s). "
                f"Maximum is {settings.MAX_DURATION_SECONDS:.0f}s.",
                error_code="AUDIO_TOO_LONG",
            )


async def validate_upload(file: UploadFile) -> tuple[bytes, AudioMetadata]:
    """
    Full validation pipeline for an uploaded audio file.
    Returns the raw bytes and extracted metadata.
    
    Raises AudioValidationError or HTTPException on failure.
    """
    # 1. Validate extension
    if not file.filename:
        raise AudioValidationError("No filename provided.", error_code="NO_FILENAME")
    ext = validate_extension(file.filename)

    # 2. Validate content type
    validate_content_type(file.content_type)

    # 3. Read file data
    data = await file.read()

    # 4. Validate file size
    validate_file_size(len(data))

    # 5. Extract and validate metadata
    meta = extract_metadata(data, ext)
    validate_duration(meta)

    return data, meta
