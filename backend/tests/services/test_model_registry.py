from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from app.core.config import Settings, settings
from app.services.model_registry import ModelRegistry, ModelUnavailableError


def test_model_is_lazy_loaded_and_reused(monkeypatch):
    registry = ModelRegistry()
    model = object()
    calls = 0

    def load():
        nonlocal calls
        calls += 1
        return model

    monkeypatch.setattr(registry, "_load_whisper", load)

    assert registry.get_status()["states"]["whisper"] == "not_loaded"
    assert calls == 0
    assert registry.get_whisper_model() is model
    assert registry.get_whisper_model() is model
    assert calls == 1
    assert registry.get_status()["states"]["whisper"] == "loaded"


def test_load_failure_is_structured_and_cached(monkeypatch):
    registry = ModelRegistry()
    calls = 0

    def fail():
        nonlocal calls
        calls += 1
        raise OSError("private local detail")

    monkeypatch.setattr(registry, "_load_whisper", fail)

    with pytest.raises(ModelUnavailableError) as first:
        registry.get_whisper_model()
    with pytest.raises(ModelUnavailableError):
        registry.get_whisper_model()

    assert first.value.error_code == "MODEL_UNAVAILABLE"
    assert calls == 1
    assert registry.get_status()["errors"]["whisper"] == "OSError: model load failed"
    assert "private local detail" not in str(first.value)


def test_concurrent_first_access_loads_once(monkeypatch):
    registry = ModelRegistry()
    model = object()
    calls = 0
    release = threading.Event()

    def load():
        nonlocal calls
        calls += 1
        release.wait(timeout=1)
        return model

    monkeypatch.setattr(registry, "_load_whisper", load)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(registry.get_whisper_model) for _ in range(4)]
        release.set()
        results = [future.result(timeout=1) for future in futures]

    assert all(result is model for result in results)
    assert calls == 1


def test_auto_device_prefers_cuda_when_available(monkeypatch):
    registry = ModelRegistry()
    monkeypatch.setattr(settings, "AI_DEVICE", "auto")
    monkeypatch.setattr(registry, "_cuda_available", lambda: True)

    assert registry.device == "cuda"


def test_auto_device_falls_back_to_cpu(monkeypatch):
    registry = ModelRegistry()
    monkeypatch.setattr(settings, "AI_DEVICE", "auto")
    monkeypatch.setattr(registry, "_cuda_available", lambda: False)

    assert registry.device == "cpu"


def test_explicit_unavailable_cuda_fails_cleanly(monkeypatch):
    registry = ModelRegistry()
    monkeypatch.setattr(settings, "AI_DEVICE", "cuda")
    monkeypatch.setattr(registry, "_cuda_available", lambda: False)

    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        _ = registry.device


def test_status_does_not_resolve_device_or_load_models():
    registry = ModelRegistry()

    status = registry.get_status()

    assert status["loaded"] == []
    assert status["selected_device"] is None
    assert status["states"] == {
        "whisper": "not_loaded",
        "emotion_ser": "not_loaded",
    }


def test_relative_runtime_paths_are_anchored_to_backend():
    configured = Settings(
        UPLOAD_DIR="runtime/uploads",
        PROCESSED_DIR="runtime/processed",
        MODEL_DIR="runtime/models",
        _env_file=None,
    )

    assert configured.UPLOAD_DIR == configured.BASE_DIR / "runtime/uploads"
    assert configured.PROCESSED_DIR == configured.BASE_DIR / "runtime/processed"
    assert configured.MODEL_DIR == configured.BASE_DIR / "runtime/models"
