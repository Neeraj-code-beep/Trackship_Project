"""Safe persistence and reusable preprocessing for driver-radio audio."""

from __future__ import annotations

import io
import math
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from backend.app.audio.decoder import decode_audio
from backend.app.audio.validation import validate_extension
from backend.app.core.config import settings
from scipy.signal import resample_poly

MODEL_SAMPLE_RATE = 16_000
SILENCE_RMS_THRESHOLD = 1e-4


@dataclass(frozen=True)
class PreprocessedAudio:
    """Original-amplitude audio plus a separate speech-model representation."""

    raw_waveform: np.ndarray
    raw_sample_rate: int
    model_waveform: np.ndarray
    model_sample_rate: int
    duration_seconds: float
    is_silent: bool
    normalization_gain: float


def _runtime_directory(path: Path) -> Path:
    directory = path.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_upload(data: bytes, original_filename: str) -> tuple[str, Path]:
    """Persist original bytes under a server-generated UUID filename."""
    ext = validate_extension(original_filename)
    upload_dir = _runtime_directory(settings.UPLOAD_DIR)

    for _ in range(3):
        file_id = str(uuid.uuid4())
        storage_path = (upload_dir / f"{file_id}{ext}").resolve()
        if storage_path.parent != upload_dir:
            raise RuntimeError("Resolved upload path escaped the upload directory.")
        try:
            with storage_path.open("xb") as output:
                output.write(data)
            return file_id, storage_path
        except FileExistsError:
            continue

    raise RuntimeError("Could not allocate a unique upload filename.")


def preprocess_audio(data: bytes, ext: str) -> PreprocessedAudio:
    """Decode once, preserve raw intensity, and prepare a normalized 16 kHz copy."""
    decoded = decode_audio(data, ext)
    raw = decoded.waveform.astype(np.float32, copy=True)
    raw_rate = decoded.info.sample_rate

    if raw_rate == MODEL_SAMPLE_RATE:
        resampled = raw.copy()
    else:
        common_divisor = math.gcd(raw_rate, MODEL_SAMPLE_RATE)
        resampled = resample_poly(
            raw,
            MODEL_SAMPLE_RATE // common_divisor,
            raw_rate // common_divisor,
        ).astype(np.float32, copy=False)

    raw_rms = _rms(raw)
    is_silent = raw_rms < SILENCE_RMS_THRESHOLD
    peak = float(np.max(np.abs(resampled))) if resampled.size else 0.0
    if is_silent or peak <= 0.0:
        gain = 1.0
        model_waveform = resampled.copy()
    else:
        gain = min(0.95 / peak, 20.0)
        model_waveform = np.clip(resampled * gain, -1.0, 1.0).astype(np.float32)

    return PreprocessedAudio(
        raw_waveform=raw,
        raw_sample_rate=raw_rate,
        model_waveform=model_waveform,
        model_sample_rate=MODEL_SAMPLE_RATE,
        duration_seconds=decoded.info.duration_seconds,
        is_silent=is_silent,
        normalization_gain=round(gain, 6),
    )


def save_processed_audio(file_id: str, audio: PreprocessedAudio) -> Path:
    """Persist the model waveform as mono 16-bit PCM WAV in the processed directory."""
    canonical_id = str(uuid.UUID(file_id))
    processed_dir = _runtime_directory(settings.PROCESSED_DIR)
    output_path = (processed_dir / f"{canonical_id}.wav").resolve()
    if output_path.parent != processed_dir:
        raise RuntimeError("Resolved processed path escaped the processed directory.")
    if output_path.exists():
        return output_path

    pcm = np.round(np.clip(audio.model_waveform, -1.0, 1.0) * 32767.0).astype("<i2")
    with output_path.open("xb") as output_file:
        with wave.open(output_file, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(audio.model_sample_rate)
            wav_file.writeframes(pcm.tobytes())
    return output_path


def extract_audio_segments(
    data: bytes,
    ext: str,
    segment_duration_seconds: float = 5.0,
) -> list[dict[str, float]]:
    """Return deterministic fixed windows with RMS measured from real audio."""
    if segment_duration_seconds <= 0:
        raise ValueError("segment_duration_seconds must be positive")

    audio = preprocess_audio(data, ext)
    total_samples = audio.raw_waveform.size
    segment_samples = max(1, round(segment_duration_seconds * audio.raw_sample_rate))
    segments: list[dict[str, float]] = []

    for start_sample in range(0, total_samples, segment_samples):
        end_sample = min(start_sample + segment_samples, total_samples)
        waveform = audio.raw_waveform[start_sample:end_sample]
        segments.append(
            {
                "start_time": round(start_sample / audio.raw_sample_rate, 3),
                "end_time": round(end_sample / audio.raw_sample_rate, 3),
                "rms_energy": round(_rms(waveform), 6),
            }
        )
    return segments


def compute_rms_energy(data: bytes, ext: str) -> float:
    """Compute full-clip RMS from decoded, original-amplitude audio."""
    return _rms(preprocess_audio(data, ext).raw_waveform)


def encode_model_wav(audio: PreprocessedAudio) -> bytes:
    """Encode model-ready audio in memory for libraries that require a WAV payload."""
    pcm = np.round(np.clip(audio.model_waveform, -1.0, 1.0) * 32767.0).astype("<i2")
    output = io.BytesIO()
    with wave.open(output, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(audio.model_sample_rate)
        wav_file.writeframes(pcm.tobytes())
    return output.getvalue()


def _rms(waveform: np.ndarray) -> float:
    if waveform.size == 0:
        return 0.0
    value = float(np.sqrt(np.mean(np.square(waveform.astype(np.float64)))))
    return value if math.isfinite(value) else 0.0
