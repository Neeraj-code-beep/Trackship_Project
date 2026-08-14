"""Codec-backed audio decoding shared by validation and preprocessing."""

from __future__ import annotations

import io
from dataclasses import dataclass

import numpy as np


class AudioDecodeError(Exception):
    """Internal decoding failure with a stable machine-readable reason."""

    def __init__(self, message: str, reason: str = "decode_failed") -> None:
        self.reason = reason
        super().__init__(message)


@dataclass(frozen=True)
class DecodedAudioInfo:
    duration_seconds: float
    sample_rate: int
    channels: int
    bit_depth: int
    container_names: frozenset[str]


@dataclass(frozen=True)
class DecodedAudio:
    waveform: np.ndarray
    info: DecodedAudioInfo


_CONTAINER_NAMES_BY_EXTENSION: dict[str, set[str]] = {
    ".wav": {"wav"},
    ".mp3": {"mp3"},
    ".m4a": {"mov", "mp4", "m4a", "3gp", "3g2", "mj2"},
    ".flac": {"flac"},
}


def inspect_audio(data: bytes, expected_ext: str) -> DecodedAudioInfo:
    """Fully decode an audio payload without retaining its waveform."""
    _, info = _decode(data, expected_ext, collect_waveform=False)
    return info


def decode_audio(data: bytes, expected_ext: str) -> DecodedAudio:
    """Decode an audio payload to an amplitude-preserving mono float waveform."""
    waveform, info = _decode(data, expected_ext, collect_waveform=True)
    if waveform is None:  # Defensive: collect_waveform=True guarantees an array.
        raise AudioDecodeError("Decoded waveform was unavailable.")
    return DecodedAudio(waveform=waveform, info=info)


def _decode(
    data: bytes,
    expected_ext: str,
    *,
    collect_waveform: bool,
) -> tuple[np.ndarray | None, DecodedAudioInfo]:
    try:
        import av
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise AudioDecodeError(
            "Audio decoding support is unavailable.",
            reason="decoder_unavailable",
        ) from exc

    if expected_ext not in _CONTAINER_NAMES_BY_EXTENSION:
        raise AudioDecodeError("Unsupported audio extension.", reason="format_mismatch")

    chunks: list[np.ndarray] = []
    try:
        with av.open(io.BytesIO(data), mode="r") as container:
            streams = [stream for stream in container.streams if stream.type == "audio"]
            if not streams:
                raise AudioDecodeError("No audio stream was found.")

            container_names = frozenset(
                name.strip().lower() for name in container.format.name.split(",")
            )
            expected_names = _CONTAINER_NAMES_BY_EXTENSION[expected_ext]
            if not container_names.intersection(expected_names):
                raise AudioDecodeError(
                    "Audio content does not match its extension.",
                    reason="format_mismatch",
                )

            stream = streams[0]
            sample_rate = int(stream.codec_context.sample_rate or 0)
            duration = 0.0
            channels = 0
            bit_depth = 0
            decoded_frames = 0

            for frame in container.decode(stream):
                frame_rate = int(frame.sample_rate or sample_rate or 0)
                if frame_rate <= 0 or frame.samples <= 0:
                    continue

                if sample_rate <= 0:
                    sample_rate = frame_rate
                if frame_rate != sample_rate:
                    raise AudioDecodeError("Audio sample rate changed during decoding.")

                decoded_frames += 1
                channels = channels or len(frame.layout.channels)
                bit_depth = bit_depth or int(getattr(frame.format, "bits", 0) or 0)
                duration += frame.samples / frame_rate

                if collect_waveform:
                    chunks.append(_frame_to_mono(frame))

            if decoded_frames == 0 or sample_rate <= 0 or duration <= 0:
                raise AudioDecodeError("No decodable audio frames were found.")

    except AudioDecodeError:
        raise
    except Exception as exc:
        raise AudioDecodeError("The audio payload could not be decoded.") from exc

    waveform: np.ndarray | None = None
    if collect_waveform:
        if not chunks:
            raise AudioDecodeError("No waveform samples were decoded.")
        waveform = np.concatenate(chunks).astype(np.float32, copy=False)
        if not np.all(np.isfinite(waveform)):
            raise AudioDecodeError("The decoded waveform contains invalid samples.")

    return waveform, DecodedAudioInfo(
        duration_seconds=round(duration, 6),
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        container_names=container_names,
    )


def _frame_to_mono(frame) -> np.ndarray:
    """Convert a decoded frame to mono without perceptual downmix gain."""
    channels = len(frame.layout.channels)
    if channels <= 0:
        raise AudioDecodeError("Decoded audio frame has no channels.")

    values = frame.to_ndarray()
    if frame.format.is_planar:
        channel_samples = values.reshape(channels, frame.samples)
    else:
        channel_samples = values.reshape(frame.samples, channels).T

    if np.issubdtype(channel_samples.dtype, np.signedinteger):
        info = np.iinfo(channel_samples.dtype)
        channel_samples = channel_samples.astype(np.float32) / max(abs(info.min), info.max)
    elif np.issubdtype(channel_samples.dtype, np.unsignedinteger):
        info = np.iinfo(channel_samples.dtype)
        midpoint = (info.max + 1) / 2.0
        channel_samples = (channel_samples.astype(np.float32) - midpoint) / midpoint
    else:
        channel_samples = channel_samples.astype(np.float32, copy=False)

    return np.mean(channel_samples, axis=0, dtype=np.float32)
