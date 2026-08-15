from __future__ import annotations

import asyncio
import io
from pathlib import Path

import pytest
from app.audio.validation import (
    AudioValidationError,
    validate_extension,
    validate_upload,
)
from app.core.config import settings
from fastapi import UploadFile


def _upload(data: bytes, filename: str = "radio.wav", content_type: str = "audio/wav"):
    return UploadFile(
        filename=filename,
        file=io.BytesIO(data),
        headers={"content-type": content_type},
    )


def test_valid_wav_is_fully_decoded(wav_bytes_factory):
    data = wav_bytes_factory(duration_seconds=1.0, sample_rate=16_000)

    returned, metadata = asyncio.run(validate_upload(_upload(data)))

    assert returned == data
    assert metadata.duration_seconds == pytest.approx(1.0, abs=0.001)
    assert metadata.sample_rate == 16_000
    assert metadata.channels == 1
    assert metadata.format_ext == ".wav"


@pytest.mark.parametrize("filename", ["clip.wav", "clip.mp3", "clip.m4a", "clip.flac"])
def test_supported_extensions(filename):
    assert validate_extension(filename) == Path(filename).suffix


def test_missing_filename_is_rejected(wav_bytes_factory):
    with pytest.raises(AudioValidationError, match="filename"):
        asyncio.run(validate_upload(_upload(wav_bytes_factory(), filename="")))


def test_unsupported_extension_is_rejected(wav_bytes_factory):
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(wav_bytes_factory(), filename="radio.txt")))
    assert captured.value.error_code == "UNSUPPORTED_AUDIO_FORMAT"


def test_mime_mismatch_is_rejected(wav_bytes_factory):
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(wav_bytes_factory(), content_type="audio/mpeg")))
    assert captured.value.error_code == "UNSUPPORTED_AUDIO_FORMAT"


def test_audio_content_must_match_extension(wav_bytes_factory):
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(
            validate_upload(
                _upload(
                    wav_bytes_factory(),
                    filename="renamed.mp3",
                    content_type="audio/mpeg",
                )
            )
        )
    assert captured.value.error_code == "UNSUPPORTED_AUDIO_FORMAT"


def test_empty_file_is_rejected():
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(b"")))
    assert captured.value.error_code == "INVALID_AUDIO"


def test_corrupted_audio_is_rejected():
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(b"RIFF this is not a wave file")))
    assert captured.value.error_code == "INVALID_AUDIO"


def test_too_short_audio_is_rejected(wav_bytes_factory):
    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(wav_bytes_factory(duration_seconds=0.1))))
    assert captured.value.error_code == "AUDIO_TOO_SHORT"


def test_oversized_audio_read_is_bounded(monkeypatch, wav_bytes_factory):
    data = wav_bytes_factory(duration_seconds=1.0)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0.001)

    with pytest.raises(AudioValidationError) as captured:
        asyncio.run(validate_upload(_upload(data)))

    assert captured.value.error_code == "AUDIO_TOO_LARGE"
    assert captured.value.status_code == 413
