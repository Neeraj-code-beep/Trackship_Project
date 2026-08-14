from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

import pytest
from app.core.config import settings
from app.schemas.schemas import (
    DriverState,
    EmotionLabel,
    EmotionProbabilities,
    LapData,
    TranscriptionResult,
    TranscriptSegment,
)
from app.services import analysis_service
from app.services.analysis_service import AnalysisPipelineError, run_full_analysis
from app.services.lap_service import normalize_laps


def _transcription(file_id):
    segments = [
        TranscriptSegment(id="seg_001", start_time=0.0, end_time=0.8, text="Okay copy"),
        TranscriptSegment(id="seg_002", start_time=0.9, end_time=1.8, text="Problem"),
        TranscriptSegment(
            id="seg_003",
            start_time=1.9,
            end_time=2.8,
            text="Box! Brake problem, losing power!",
        ),
    ]
    return TranscriptionResult(
        file_id=file_id,
        full_text=" ".join(segment.text for segment in segments),
        segments=segments,
        language="en",
        duration_seconds=3.0,
        detected_speech=True,
    )


def _emotion_states(segments):
    stress_values = [0.2, 0.6, 0.9]
    states = []
    for segment, stress in zip(segments, stress_values, strict=True):
        states.append(
            DriverState(
                segment_id=segment.id,
                timestamp=segment.start_time,
                start_time=segment.start_time,
                end_time=segment.end_time,
                dominant_emotion=EmotionLabel.STRESSED,
                probabilities=EmotionProbabilities(
                    stressed=stress,
                    neutral=1.0 - stress,
                ),
                raw_emotions={"angry": stress, "neutral": 1.0 - stress},
                confidence=max(stress, 1.0 - stress),
            )
        )
    return states


def test_mocked_ai_full_pipeline_wiring(
    tmp_path,
    monkeypatch,
    wav_bytes_factory,
):
    file_id = str(uuid.uuid4())
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    upload_dir.mkdir()
    (upload_dir / f"{file_id}.wav").write_bytes(
        wav_bytes_factory(duration_seconds=3.0, amplitude=0.2)
    )
    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(settings, "PROCESSED_DIR", processed_dir)

    async def fake_transcription(audio, requested_file_id):
        assert audio.duration_seconds == 3.0
        return _transcription(requested_file_id)

    async def fake_emotions(audio, segments):
        assert audio.model_sample_rate == 16_000
        return _emotion_states(segments)

    monkeypatch.setattr(analysis_service, "transcribe_preprocessed", fake_transcription)
    monkeypatch.setattr(analysis_service, "analyze_preprocessed_emotions", fake_emotions)
    laps = normalize_laps(
        [
            LapData(lap_number=1, lap_time_seconds=0.9),
            LapData(lap_number=2, lap_time_seconds=1.0),
            LapData(lap_number=3, lap_time_seconds=1.1),
        ]
    )
    race_store = {
        "race-1": {
            "race_id": "race-1",
            "driver_name": "Driver",
            "laps": laps,
            "analyses": [],
            "created_at": datetime.now(timezone.utc),
        }
    }

    result = asyncio.run(
        run_full_analysis(file_id=file_id, race_id="race-1", race_store=race_store)
    )

    assert result.analysis_id.startswith("analysis_")
    assert result.audio_id == file_id
    assert result.summary.segments_analyzed == 3
    assert len(result.transcription.segments) == 3
    assert len(result.acoustic_analysis.segments) == 3
    assert len(result.driver_states) == 3
    assert len(result.aligned_laps) == 3
    assert result.aligned_laps[2].lap_delta == pytest.approx(0.1)
    assert result.correlations.stress_vs_lap_delta.pearson_r is not None
    assert all(insight.evidence for insight in result.insights)
    assert race_store["race-1"]["analyses"] == [result.analysis_id]
    assert (processed_dir / f"{file_id}.wav").exists()
    json.dumps(result.model_dump(mode="json"), allow_nan=False)


def test_missing_audio_id_returns_resource_error(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    with pytest.raises(AnalysisPipelineError) as captured:
        asyncio.run(
            run_full_analysis(
                file_id=str(uuid.uuid4()),
                race_id=None,
                race_store={},
            )
        )

    assert captured.value.error_code == "AUDIO_NOT_FOUND"
    assert captured.value.status_code == 404


def test_unknown_race_is_rejected_before_ai_work(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    with pytest.raises(AnalysisPipelineError) as captured:
        asyncio.run(
            run_full_analysis(
                file_id=str(uuid.uuid4()),
                race_id="missing-race",
                race_store={},
            )
        )

    assert captured.value.error_code == "RACE_NOT_FOUND"
