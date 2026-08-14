"""
Pydantic schemas for Silent Co-Driver API contracts.
All request/response models are defined here for strict type safety.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


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
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
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


class DriverState(BaseModel):
    timestamp: float = Field(description="Seconds from start of audio")
    dominant_emotion: EmotionLabel
    probabilities: EmotionProbabilities
    confidence: float = Field(ge=0.0, le=1.0)
    rms_energy: Optional[float] = None
    speech_rate_wpm: Optional[float] = None


# ─── Transcription Schemas ────────────────────────────────────────────────────

class TranscriptSegment(BaseModel):
    start_time: float
    end_time: float
    text: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
    speaker: Optional[str] = None


class TranscriptionResult(BaseModel):
    file_id: str
    full_text: str
    segments: list[TranscriptSegment] = []
    language: str = "en"
    duration_seconds: float = 0.0


# ─── Lap / Race Schemas ──────────────────────────────────────────────────────

class LapData(BaseModel):
    lap_number: int = Field(ge=1)
    lap_time_seconds: float = Field(gt=0)
    sector_1: Optional[float] = None
    sector_2: Optional[float] = None
    sector_3: Optional[float] = None
    timestamp: Optional[float] = Field(
        default=None, description="Race clock timestamp when lap completed"
    )
    tyre_compound: Optional[str] = None
    fuel_load_kg: Optional[float] = None


class LapIngestionRequest(BaseModel):
    race_id: str
    driver_name: str
    laps: list[LapData]


class LapIngestionResponse(BaseModel):
    race_id: str
    driver_name: str
    laps_received: int
    message: str = "Lap data ingested successfully"


# ─── Analysis Schemas ─────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    file_id: str
    race_id: Optional[str] = None


class AlignedLapEmotion(BaseModel):
    lap_number: int
    lap_time_seconds: float
    delta_to_best: float = 0.0
    dominant_emotion: EmotionLabel
    stress_level: float = Field(ge=0.0, le=1.0, default=0.0)
    fatigue_level: float = Field(ge=0.0, le=1.0, default=0.0)


class InsightItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: InsightSeverity
    category: str
    message: str
    lap_number: Optional[int] = None
    timestamp: Optional[float] = None
    data: Optional[dict] = None


class AnalysisResponse(BaseModel):
    file_id: str
    race_id: Optional[str] = None
    transcription: Optional[TranscriptionResult] = None
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
    best_lap_time: Optional[float] = None
    average_lap_time: Optional[float] = None
    laps: list[LapData] = []
    analyses: list[str] = Field(
        default_factory=list, description="List of analysis file_ids linked"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ─── Generic ─────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
