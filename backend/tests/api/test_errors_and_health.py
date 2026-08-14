from __future__ import annotations

import uuid

from app.api.routes import _stores
from app.api.routes import analysis as analysis_route
from app.main import app
from app.services.transcription_service import TranscriptionError
from fastapi.testclient import TestClient


def setup_function():
    _stores.race_store.clear()


def teardown_function():
    _stores.race_store.clear()


def test_versioned_health_is_lightweight_and_legacy_alias_remains():
    client = TestClient(app)

    versioned = client.get("/api/v1/health")
    legacy = client.get("/health")

    assert versioned.status_code == 200
    assert legacy.status_code == 200
    assert versioned.json()["status"] == "ok"
    assert versioned.json()["version"] == "0.2.0"
    assert set(versioned.json()["models"]["states"]) == {"whisper", "emotion_ser"}


def test_request_id_is_echoed_on_success_and_error():
    client = TestClient(app, raise_server_exceptions=False)

    success = client.get("/api/v1/health", headers={"x-request-id": "test-request-123"})
    failure = client.get(
        "/api/v1/race/missing",
        headers={"x-request-id": "test-request-456"},
    )

    assert success.headers["x-request-id"] == "test-request-123"
    assert failure.headers["x-request-id"] == "test-request-456"
    assert failure.json()["error"]["request_id"] == "test-request-456"


def test_missing_audio_returns_stable_nested_error():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/analysis",
        json={"file_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "The requested audio file was not found."
    assert response.json()["error_code"] == "AUDIO_NOT_FOUND"
    assert response.json()["error"]["code"] == "AUDIO_NOT_FOUND"


def test_race_not_found_uses_race_error_code():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/v1/race/not-there")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RACE_NOT_FOUND"


def test_request_validation_error_does_not_echo_raw_input():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/v1/analysis", json={"unexpected": "private-value"})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert body["error"]["details"]
    assert "private-value" not in response.text


def test_model_unavailable_error_is_structured(monkeypatch):
    async def unavailable(**kwargs):
        raise TranscriptionError(
            "The transcription model is unavailable.",
            error_code="MODEL_UNAVAILABLE",
            status_code=503,
        )

    monkeypatch.setattr(analysis_route, "run_full_analysis", unavailable)
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/analysis",
        json={"file_id": str(uuid.uuid4())},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "MODEL_UNAVAILABLE"
