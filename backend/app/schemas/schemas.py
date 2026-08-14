"""
Pydantic schemas for Silent Co-Driver API contracts.
All request/response models are defined here for strict type safety.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ─── Enums ────────────────────────────────────────────────────────────────────


class EmotionLabel(str, Enum):
    CALM = "calm"
    STRESSED = "stressed"
    NEUTRAL = "neutral"
    TIRED = "tired"


class InsightSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ─── Audio Schemas ────────────────────────────────────────────────────────────


class AudioUploadResponse(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_size_bytes: int
    duration_seconds: float | None = None
    sample_rate: int | None = None
    format: str
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)
    storage_path: str
    message: str = "Audio file uploaded successfully"


# ─── Emotion / Driver State Schemas ──────────────────────────────────────────


class EmotionProbabilities(BaseModel):
    calm: float = Field(ge=0.0, le=1.0, default=0.0)
    stressed: float = Field(ge=0.0, le=1.0, default=0.0)
    neutral: float = Field(ge=0.0, le=1.0, default=0.0)
    tired: float = Field(ge=0.0, le=1.0, default=0.0)


class AcousticFeatures(BaseModel):
    rms_energy: float = Field(ge=0.0)
    pitch_mean_hz: float | None = Field(default=None, ge=0.0)
    pitch_std_hz: float | None = Field(default=None, ge=0.0)
    zero_crossing_rate: float = Field(ge=0.0, le=1.0)
    spectral_centroid_hz: float = Field(ge=0.0)
    duration_seconds: float = Field(ge=0.0)
    pause_ratio: float = Field(ge=0.0, le=1.0)
    speech_rate_wpm: float | None = Field(default=None, ge=0.0)
    voiced_ratio: float = Field(ge=0.0, le=1.0)
    energy_variability: float = Field(ge=0.0)


class DriverState(BaseModel):
    segment_id: str | None = None
    timestamp: float = Field(description="Seconds from start of audio")
    start_time: float | None = None
    end_time: float | None = None
    dominant_emotion: EmotionLabel
    probabilities: EmotionProbabilities
    raw_emotions: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0)
    stress_score: float = Field(default=0.0, ge=0.0, le=100.0)
    fatigue_score: float = Field(default=0.0, ge=0.0, le=100.0)
    calm_score: float = Field(default=0.0, ge=0.0, le=100.0)
    signals: dict[str, float] = Field(default_factory=dict)
    drivers: list[str] = Field(default_factory=list)
    acoustic_features: AcousticFeatures | None = None
    rms_energy: float | None = None
    speech_rate_wpm: float | None = None


# ─── Transcription Schemas ────────────────────────────────────────────────────


class TranscriptSegment(BaseModel):
    id: str
    start_time: float
    end_time: float
    text: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    speaker: str | None = None


class TranscriptionResult(BaseModel):
    file_id: str
    full_text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str | None = None
    duration_seconds: float = 0.0
    detected_speech: bool = False


class SegmentAcousticFeatures(BaseModel):
    segment_id: str
    start_time: float
    end_time: float
    features: AcousticFeatures
    session_deviations: dict[str, float] = Field(default_factory=dict)


class AcousticAnalysis(BaseModel):
    session_baselines: dict[str, float] = Field(default_factory=dict)
    segments: list[SegmentAcousticFeatures] = Field(default_factory=list)


# ─── Lap / Race Schemas ──────────────────────────────────────────────────────


class LapData(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    lap_number: int = Field(ge=1)
    lap_time_seconds: float = Field(gt=0, le=3600)
    start_time: float | None = Field(default=None, ge=0)
    end_time: float | None = Field(default=None, gt=0)
    sector_1: float | None = None
    sector_2: float | None = None
    sector_3: float | None = None
    timestamp: float | None = Field(
        default=None, description="Race clock timestamp when lap completed"
    )
    tyre_compound: str | None = None
    fuel_load_kg: float | None = None


class LapIngestionRequest(BaseModel):
    race_id: str = Field(min_length=1, max_length=100)
    driver_name: str = Field(min_length=1, max_length=100)
    laps: list[LapData] = Field(min_length=1, max_length=10_000)


class LapIngestionResponse(BaseModel):
    race_id: str
    driver_name: str
    laps_received: int
    message: str = "Lap data ingested successfully"


# ─── Analysis Schemas ─────────────────────────────────────────────────────────


class AnalysisRequest(BaseModel):
    file_id: str
    race_id: str | None = None


class AlignedLapEmotion(BaseModel):
    lap_number: int
    lap_time_seconds: float
    start_time: float = 0.0
    end_time: float = 0.0
    delta_to_best: float = 0.0
    dominant_emotion: EmotionLabel
    stress_level: float = Field(ge=0.0, le=1.0, default=0.0)
    fatigue_level: float = Field(ge=0.0, le=1.0, default=0.0)
    stress_score: float = Field(ge=0.0, le=100.0, default=0.0)
    fatigue_score: float = Field(ge=0.0, le=100.0, default=0.0)
    calm_score: float = Field(ge=0.0, le=100.0, default=0.0)
    segment_ids: list[str] = Field(default_factory=list)


class InsightItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: InsightSeverity
    category: str
    message: str
    lap_number: int | None = None
    timestamp: float | None = None
    data: dict | None = None


class AnalysisResponse(BaseModel):
    file_id: str
    race_id: str | None = None
    transcription: TranscriptionResult | None = None
    driver_states: list[DriverState] = []
    aligned_laps: list[AlignedLapEmotion] = []
    insights: list[InsightItem] = []
    overall_stress: float = 0.0
    overall_fatigue: float = 0.0
    processing_time_ms: float = 0.0


# ─── Race Retrieval ──────────────────────────────────────────────────────────


class RaceOverview(BaseModel):
    race_id: str
    driver_name: str
    total_laps: int
    best_lap_time: float | None = None
    average_lap_time: float | None = None
    laps: list[LapData] = []
    analyses: list[str] = Field(
        default_factory=list, description="List of analysis file_ids linked"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Generic ─────────────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
