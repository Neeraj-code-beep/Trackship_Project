"""Validation for uploaded driver-radio audio."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.audio.decoder import AudioDecodeError, inspect_audio
from app.core.config import settings
from fastapi import UploadFile


class AudioValidationError(Exception):
    """A safe, client-facing audio validation failure."""

    def __init__(
        self,
        message: str,
        error_code: str = "INVALID_AUDIO",
        status_code: int = 400,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class AudioMetadata:
    """Metadata proven by decoding the uploaded audio."""

    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    file_size_bytes: int
    format_ext: str


_MIME_TYPES_BY_EXTENSION: dict[str, set[str]] = {
    ".wav": {"audio/wav", "audio/x-wav", "audio/wave"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".m4a": {"audio/m4a", "audio/x-m4a", "audio/mp4"},
    ".flac": {"audio/flac", "audio/x-flac"},
}


def validate_extension(filename: str) -> str:
    """Return the normalized extension when it is supported."""
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
        raise AudioValidationError(
            f"Unsupported audio format '{ext or 'missing'}'. Allowed: {allowed}.",
            error_code="UNSUPPORTED_AUDIO_FORMAT",
        )
    return ext


def validate_content_type(content_type: str | None, ext: str) -> None:
    """Validate a reliable MIME type against the claimed extension."""
    if not content_type or content_type == "application/octet-stream":
        return

    normalized = content_type.split(";", maxsplit=1)[0].strip().lower()
    expected = _MIME_TYPES_BY_EXTENSION[ext]
    if normalized not in expected:
        raise AudioValidationError(
            f"Content type '{normalized}' does not match the '{ext}' audio format.",
            error_code="UNSUPPORTED_AUDIO_FORMAT",
        )


def validate_file_size(size_bytes: int) -> None:
    """Reject empty or oversized payloads."""
    if size_bytes <= 0:
        raise AudioValidationError("The uploaded audio file is empty.")
    if size_bytes > settings.max_upload_size_bytes:
        raise AudioValidationError(
            f"Audio exceeds the {settings.MAX_UPLOAD_SIZE_MB:g} MB upload limit.",
            error_code="AUDIO_TOO_LARGE",
            status_code=413,
        )


def _decoded_metadata(data: bytes, ext: str) -> AudioMetadata:
    try:
        decoded = inspect_audio(data, ext)
    except AudioDecodeError as exc:
        if exc.reason == "decoder_unavailable":
            raise AudioValidationError(
                "Audio decoding support is unavailable on the server.",
                error_code="AUDIO_DECODER_UNAVAILABLE",
                status_code=503,
            ) from exc
        if exc.reason == "format_mismatch":
            raise AudioValidationError(
                "The file content does not match its audio extension.",
                error_code="UNSUPPORTED_AUDIO_FORMAT",
            ) from exc
        raise AudioValidationError(
            "The uploaded audio file could not be decoded.",
            error_code="INVALID_AUDIO",
        ) from exc

    return AudioMetadata(
        duration_seconds=decoded.duration_seconds,
        sample_rate=decoded.sample_rate,
        channels=decoded.channels,
        bit_depth=decoded.bit_depth,
        file_size_bytes=len(data),
        format_ext=ext,
    )


def validate_duration(metadata: AudioMetadata) -> None:
    """Enforce configured duration bounds on decoded audio."""
    duration = metadata.duration_seconds
    if duration < settings.MIN_AUDIO_DURATION_SECONDS:
        raise AudioValidationError(
            f"Audio is too short ({duration:.2f}s); minimum is "
            f"{settings.MIN_AUDIO_DURATION_SECONDS:g}s.",
            error_code="AUDIO_TOO_SHORT",
        )
    if duration > settings.MAX_AUDIO_DURATION_SECONDS:
        raise AudioValidationError(
            f"Audio is too long ({duration:.1f}s); maximum is "
            f"{settings.MAX_AUDIO_DURATION_SECONDS:g}s.",
            error_code="AUDIO_TOO_LONG",
        )


async def validate_upload(file: UploadFile) -> tuple[bytes, AudioMetadata]:
    """Read a bounded payload, decode it, and return verified metadata."""
    if not file.filename:
        raise AudioValidationError("No audio filename was provided.")

    ext = validate_extension(file.filename)
    validate_content_type(file.content_type, ext)

    data = await file.read(settings.max_upload_size_bytes + 1)
    validate_file_size(len(data))

    metadata = _decoded_metadata(data, ext)
    validate_duration(metadata)
    return data, metadata
