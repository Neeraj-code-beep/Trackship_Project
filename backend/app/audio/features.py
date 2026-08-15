"""Interpretable acoustic features extracted from real waveform segments."""

from __future__ import annotations

import math
import re

import numpy as np
from app.audio.preprocessing import PreprocessedAudio
from app.schemas.schemas import (
    AcousticAnalysis,
    AcousticFeatures,
    SegmentAcousticFeatures,
    TranscriptSegment,
)

PITCH_MIN_HZ = 70.0
PITCH_MAX_HZ = 400.0
PITCH_CORRELATION_THRESHOLD = 0.3
FRAME_SECONDS = 0.03
HOP_SECONDS = 0.01
SILENCE_ABSOLUTE_RMS = 1e-4


def analyze_acoustics(
    audio: PreprocessedAudio,
    segments: list[TranscriptSegment],
) -> AcousticAnalysis:
    """Extract per-transcript features and same-session robust baselines."""
    records: list[SegmentAcousticFeatures] = []
    for segment in segments:
        start_sample = max(0, round(segment.start_time * audio.raw_sample_rate))
        end_sample = min(
            audio.raw_waveform.size,
            round(segment.end_time * audio.raw_sample_rate),
        )
        waveform = audio.raw_waveform[start_sample:end_sample]
        if waveform.size == 0:
            continue
        records.append(
            SegmentAcousticFeatures(
                segment_id=segment.id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                features=extract_acoustic_features(
                    waveform,
                    audio.raw_sample_rate,
                    text=segment.text,
                ),
            )
        )

    baselines, deviations = _session_deviations(records)
    for record in records:
        record.session_deviations = deviations.get(record.segment_id, {})
    return AcousticAnalysis(session_baselines=baselines, segments=records)


def extract_acoustic_features(
    waveform: np.ndarray,
    sample_rate: int,
    *,
    text: str | None = None,
) -> AcousticFeatures:
    """Calculate a compact, finite feature set for one audio segment."""
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")

    samples = np.asarray(waveform, dtype=np.float32).reshape(-1)
    samples = np.nan_to_num(samples, nan=0.0, posinf=0.0, neginf=0.0)
    duration = samples.size / sample_rate
    frames = _frame_signal(samples, sample_rate)
    frame_rms = np.asarray([_rms(frame) for frame in frames], dtype=np.float64)

    rms_energy = _rms(samples)
    energy_variability = float(np.std(frame_rms)) if frame_rms.size else 0.0
    pause_threshold = max(
        SILENCE_ABSOLUTE_RMS,
        (float(np.max(frame_rms)) * 0.1) if frame_rms.size else 0.0,
    )
    pause_ratio = float(np.mean(frame_rms < pause_threshold)) if frame_rms.size else 1.0

    pitches = [
        pitch for frame in frames if (pitch := _estimate_pitch(frame, sample_rate)) is not None
    ]
    pitch_mean = float(np.mean(pitches)) if pitches else None
    pitch_std = float(np.std(pitches)) if pitches else None
    voiced_ratio = len(pitches) / len(frames) if frames else 0.0

    if samples.size > 1:
        zero_crossing_rate = float(np.mean((samples[:-1] * samples[1:]) < 0.0))
    else:
        zero_crossing_rate = 0.0

    spectral_centroid = _spectral_centroid(samples, sample_rate)
    word_count = len(re.findall(r"\b[\w']+\b", text or ""))
    speech_rate = (word_count / duration * 60.0) if duration > 0 and text is not None else None

    return AcousticFeatures(
        rms_energy=_finite(rms_energy),
        pitch_mean_hz=_optional_finite(pitch_mean),
        pitch_std_hz=_optional_finite(pitch_std),
        zero_crossing_rate=_bounded(zero_crossing_rate),
        spectral_centroid_hz=max(_finite(spectral_centroid), 0.0),
        duration_seconds=max(_finite(duration), 0.0),
        pause_ratio=_bounded(pause_ratio),
        speech_rate_wpm=_optional_nonnegative(speech_rate),
        voiced_ratio=_bounded(voiced_ratio),
        energy_variability=max(_finite(energy_variability), 0.0),
    )


def _frame_signal(waveform: np.ndarray, sample_rate: int) -> list[np.ndarray]:
    if waveform.size == 0:
        return []
    frame_length = max(1, round(FRAME_SECONDS * sample_rate))
    hop_length = max(1, round(HOP_SECONDS * sample_rate))
    if waveform.size <= frame_length:
        return [waveform]
    starts = list(range(0, waveform.size - frame_length + 1, hop_length))
    frames = [waveform[start : start + frame_length] for start in starts]
    final_start = waveform.size - frame_length
    if not starts or starts[-1] != final_start:
        frames.append(waveform[final_start:])
    return frames


def _estimate_pitch(frame: np.ndarray, sample_rate: int) -> float | None:
    min_lag = max(1, math.floor(sample_rate / PITCH_MAX_HZ))
    max_lag = min(frame.size - 1, math.ceil(sample_rate / PITCH_MIN_HZ))
    if frame.size < 2 or max_lag <= min_lag or _rms(frame) < SILENCE_ABSOLUTE_RMS:
        return None

    centered = frame.astype(np.float64) - float(np.mean(frame))
    windowed = centered * np.hanning(centered.size)
    fft_size = 1 << (2 * centered.size - 1).bit_length()
    spectrum = np.fft.rfft(windowed, n=fft_size)
    correlation = np.fft.irfft(spectrum * np.conjugate(spectrum), n=fft_size)[: centered.size]
    if correlation[0] <= 0:
        return None

    search = correlation[min_lag : max_lag + 1]
    lag = int(np.argmax(search)) + min_lag
    strength = float(correlation[lag] / correlation[0])
    if strength < PITCH_CORRELATION_THRESHOLD:
        return None
    pitch = sample_rate / lag
    return pitch if math.isfinite(pitch) else None


def _spectral_centroid(waveform: np.ndarray, sample_rate: int) -> float:
    if waveform.size < 2 or _rms(waveform) < SILENCE_ABSOLUTE_RMS:
        return 0.0
    centered = waveform.astype(np.float64) - float(np.mean(waveform))
    magnitudes = np.abs(np.fft.rfft(centered * np.hanning(centered.size)))
    magnitude_sum = float(np.sum(magnitudes))
    if magnitude_sum <= 0:
        return 0.0
    frequencies = np.fft.rfftfreq(centered.size, d=1.0 / sample_rate)
    return float(np.sum(frequencies * magnitudes) / magnitude_sum)


def _session_deviations(
    records: list[SegmentAcousticFeatures],
) -> tuple[dict[str, float], dict[str, dict[str, float]]]:
    metrics = (
        "rms_energy",
        "pitch_std_hz",
        "speech_rate_wpm",
        "pause_ratio",
        "energy_variability",
    )
    baselines: dict[str, float] = {}
    scales: dict[str, float] = {}

    for metric in metrics:
        values = [
            float(value)
            for record in records
            if (value := getattr(record.features, metric)) is not None
            and math.isfinite(float(value))
        ]
        if not values:
            continue
        median = float(np.median(values))
        mad = float(np.median(np.abs(np.asarray(values) - median)))
        baselines[metric] = round(median, 6)
        scales[metric] = max(1.4826 * mad, abs(median) * 0.1, 1e-6)

    deviations: dict[str, dict[str, float]] = {}
    for record in records:
        relative: dict[str, float] = {}
        for metric, baseline in baselines.items():
            value = getattr(record.features, metric)
            if value is None or not math.isfinite(float(value)):
                continue
            robust_score = (float(value) - baseline) / scales[metric]
            relative[metric] = round(math.tanh(robust_score / 2.0), 6)
        deviations[record.segment_id] = relative
    return baselines, deviations


def _rms(waveform: np.ndarray) -> float:
    if waveform.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(waveform.astype(np.float64)))))


def _finite(value: float) -> float:
    return float(value) if math.isfinite(float(value)) else 0.0


def _optional_finite(value: float | None) -> float | None:
    return _finite(value) if value is not None and math.isfinite(float(value)) else None


def _optional_nonnegative(value: float | None) -> float | None:
    sanitized = _optional_finite(value)
    return max(sanitized, 0.0) if sanitized is not None else None


def _bounded(value: float) -> float:
    return min(max(_finite(value), 0.0), 1.0)
