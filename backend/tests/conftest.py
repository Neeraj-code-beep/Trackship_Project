from __future__ import annotations

import io
import math
import struct
import wave

import pytest


@pytest.fixture
def wav_bytes_factory():
    def build(
        duration_seconds: float = 1.0,
        sample_rate: int = 16_000,
        frequency_hz: float = 220.0,
        amplitude: float = 0.2,
    ) -> bytes:
        frame_count = int(duration_seconds * sample_rate)
        samples = [
            int(32767 * amplitude * math.sin(2 * math.pi * frequency_hz * i / sample_rate))
            for i in range(frame_count)
        ]
        output = io.BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        return output.getvalue()

    return build
