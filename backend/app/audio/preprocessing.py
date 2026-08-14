"""
Audio preprocessing module.
Handles safe temporary file storage, normalization, and feature extraction.
"""

from __future__ import annotations

import os
import uuid
import struct
import wave
import io
import math
import tempfile
from pathlib import Path
from typing import Optional

from backend.app.core.config import settings
from backend.app.audio.validation import AudioMetadata


def save_upload(data: bytes, original_filename: str) -> tuple[str, Path]:
    """
    Save uploaded audio data to the uploads directory with a unique ID.
    Returns (file_id, storage_path).
    """
    file_id = str(uuid.uuid4())
    ext = Path(original_filename).suffix.lower()
    safe_name = f"{file_id}{ext}"
    storage_path = settings.UPLOAD_DIR / safe_name
    storage_path.write_bytes(data)
    return file_id, storage_path


def compute_rms_energy(data: bytes, ext: str) -> float:
    """
    Compute RMS energy of an audio file.
    Currently supports WAV files natively; returns estimate for others.
    """
    if ext == ".wav":
        try:
            buf = io.BytesIO(data)
            with wave.open(buf, "rb") as wf:
                n_frames = wf.getnframes()
                if n_frames == 0:
                    return 0.0
                sample_width = wf.getsampwidth()
                raw_frames = wf.readframes(min(n_frames, 44100 * 5))  # First 5s sample

                if sample_width == 2:
                    fmt = f"<{len(raw_frames) // 2}h"
                    samples = struct.unpack(fmt, raw_frames)
                    max_val = 32768.0
                elif sample_width == 1:
                    samples = [b - 128 for b in raw_frames]
                    max_val = 128.0
                else:
                    return 0.5  # fallback

                if not samples:
                    return 0.0

                sum_sq = sum(s * s for s in samples)
                rms = math.sqrt(sum_sq / len(samples)) / max_val
                return min(rms, 1.0)
        except Exception:
            return 0.5  # fallback on error
    else:
        # For non-WAV formats, return a reasonable estimate
        # In production, would use ffmpeg/pydub to decode first
        return 0.5


def normalize_audio_data(data: bytes, ext: str) -> bytes:
    """
    Basic audio normalization for WAV files.
    For non-WAV formats, returns data unchanged (would need ffmpeg in production).
    """
    if ext != ".wav":
        return data

    try:
        buf = io.BytesIO(data)
        with wave.open(buf, "rb") as wf:
            params = wf.getparams()
            n_frames = wf.getnframes()
            if n_frames == 0 or params.sampwidth != 2:
                return data

            raw = wf.readframes(n_frames)
            fmt = f"<{len(raw) // 2}h"
            samples = list(struct.unpack(fmt, raw))

            # Find peak
            peak = max(abs(s) for s in samples) if samples else 1
            if peak == 0:
                return data

            # Normalize to 90% of max to avoid clipping
            scale = (32767 * 0.9) / peak
            normalized = [int(s * scale) for s in samples]
            normalized_raw = struct.pack(f"<{len(normalized)}h", *normalized)

            # Rebuild WAV
            out = io.BytesIO()
            with wave.open(out, "wb") as wf_out:
                wf_out.setparams(params)
                wf_out.writeframes(normalized_raw)
            return out.getvalue()
    except Exception:
        return data


def extract_audio_segments(
    data: bytes, ext: str, segment_duration_seconds: float = 5.0
) -> list[dict]:
    """
    Split audio into fixed-duration segments for analysis.
    Returns list of dicts with start_time, end_time, and rms_energy.
    """
    segments = []

    if ext == ".wav":
        try:
            buf = io.BytesIO(data)
            with wave.open(buf, "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                sample_width = wf.getsampwidth()
                total_duration = n_frames / sample_rate if sample_rate > 0 else 0
                frames_per_segment = int(segment_duration_seconds * sample_rate)

                offset = 0
                while offset < n_frames:
                    chunk_frames = min(frames_per_segment, n_frames - offset)
                    wf.setpos(offset)
                    raw = wf.readframes(chunk_frames)

                    start_t = offset / sample_rate
                    end_t = (offset + chunk_frames) / sample_rate

                    # Compute RMS for this segment
                    if sample_width == 2 and len(raw) >= 2:
                        fmt = f"<{len(raw) // 2}h"
                        samples = struct.unpack(fmt, raw)
                        if samples:
                            sum_sq = sum(s * s for s in samples)
                            rms = math.sqrt(sum_sq / len(samples)) / 32768.0
                        else:
                            rms = 0.0
                    else:
                        rms = 0.5

                    segments.append({
                        "start_time": round(start_t, 3),
                        "end_time": round(end_t, 3),
                        "rms_energy": round(min(rms, 1.0), 4),
                    })
                    offset += chunk_frames
        except Exception:
            # Fallback: estimate from file size
            assumed_duration = len(data) / (44100 * 2 * 2)  # 44.1k, 16-bit, stereo
            n_segs = max(1, int(assumed_duration / segment_duration_seconds))
            for i in range(n_segs):
                segments.append({
                    "start_time": round(i * segment_duration_seconds, 3),
                    "end_time": round((i + 1) * segment_duration_seconds, 3),
                    "rms_energy": 0.5,
                })
    else:
        # For non-WAV: rough estimate based on assumed duration
        assumed_bitrate = 128_000
        assumed_duration = (len(data) * 8) / assumed_bitrate
        n_segs = max(1, int(assumed_duration / segment_duration_seconds))
        for i in range(n_segs):
            segments.append({
                "start_time": round(i * segment_duration_seconds, 3),
                "end_time": round(min((i + 1) * segment_duration_seconds, assumed_duration), 3),
                "rms_energy": 0.5,
            })

    return segments


def cleanup_temp_file(path: Path) -> None:
    """Safely remove a temporary file if it exists."""
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass
