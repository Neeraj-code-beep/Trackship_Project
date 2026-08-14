from __future__ import annotations

from backend.app.core.config import settings
from backend.app.main import app
from fastapi.testclient import TestClient


def test_audio_upload_accepts_valid_wav(tmp_path, monkeypatch, wav_bytes_factory):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/v1/audio/upload",
        files={"file": ("radio.wav", wav_bytes_factory(), "audio/wav")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["format"] == "wav"
    assert body["duration_seconds"] == 1.0
    assert body["storage_path"] == f"data/uploads/{body['file_id']}.wav"
    assert (tmp_path / f"{body['file_id']}.wav").exists()


def test_audio_upload_returns_validation_code_for_corrupt_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.post(
        "/api/v1/audio/upload",
        files={"file": ("radio.wav", b"not audio", "audio/wav")},
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_AUDIO"
