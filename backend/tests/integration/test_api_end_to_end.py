from __future__ import annotations

import json
import math

from app.api.routes import _stores
from app.core.config import settings
from app.main import app
from app.services.model_registry import registry
from fastapi.testclient import TestClient


class StubWhisper:
    def transcribe(self, waveform, **options):
        assert len(waveform) == 48_000
        assert options["fp16"] is False
        return {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 0.8, "text": "Okay copy", "avg_logprob": math.log(0.9)},
                {"start": 0.9, "end": 1.8, "text": "Problem", "avg_logprob": math.log(0.8)},
                {
                    "start": 1.9,
                    "end": 2.8,
                    "text": "Box brake problem losing power",
                    "avg_logprob": math.log(0.85),
                },
            ],
        }


class StubEmotion:
    def __call__(self, waveforms, **options):
        assert len(waveforms) == 3
        assert options["top_k"] is None
        return [
            [{"label": "neutral", "score": 0.8}, {"label": "angry", "score": 0.2}],
            [{"label": "neutral", "score": 0.4}, {"label": "angry", "score": 0.6}],
            [{"label": "neutral", "score": 0.1}, {"label": "angry", "score": 0.9}],
        ]


def test_http_end_to_end_pipeline_without_model_downloads(
    tmp_path,
    monkeypatch,
    wav_bytes_factory,
):
    _stores.race_store.clear()
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(settings, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(registry, "get_whisper_model", lambda: StubWhisper())
    monkeypatch.setattr(registry, "get_emotion_model", lambda: StubEmotion())
    monkeypatch.setattr(registry, "_device", "cpu")
    client = TestClient(app, raise_server_exceptions=False)

    upload = client.post(
        "/api/v1/audio/upload",
        files={
            "file": (
                "radio.wav",
                wav_bytes_factory(duration_seconds=3.0),
                "audio/wav",
            )
        },
    )
    assert upload.status_code == 200
    file_id = upload.json()["file_id"]

    laps = client.post(
        "/api/v1/race/laps",
        json={
            "race_id": "e2e-race",
            "driver_name": "Test Driver",
            "laps": [
                {"lap_number": 1, "lap_time_seconds": 0.9},
                {"lap_number": 2, "lap_time_seconds": 1.0},
                {"lap_number": 3, "lap_time_seconds": 1.1},
            ],
        },
    )
    assert laps.status_code == 200

    analysis = client.post(
        "/api/v1/analysis",
        json={"file_id": file_id, "race_id": "e2e-race"},
    )
    assert analysis.status_code == 200, analysis.text
    body = analysis.json()
    assert body["transcription"]["detected_speech"] is True
    assert body["transcription"]["full_text"].startswith("Okay copy")
    assert len(body["driver_states"]) == 3
    assert len(body["acoustic_analysis"]["segments"]) == 3
    assert len(body["aligned_laps"]) == 3
    assert body["aligned_laps"][2]["lap_delta"] == 0.1
    assert body["correlations"]["stress_vs_lap_delta"]["pearson_r"] is not None
    assert all(item["evidence"] for item in body["insights"])
    json.dumps(body, allow_nan=False)

    race = client.get("/api/v1/race/e2e-race")
    assert race.status_code == 200
    assert race.json()["analyses"] == [body["analysis_id"]]
    assert (processed_dir / f"{file_id}.wav").exists()
    _stores.race_store.clear()
