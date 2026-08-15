from __future__ import annotations

from app.core.config import Settings


def test_cors_origins_accepts_json_list(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        '["http://localhost:5173", "http://127.0.0.1:5173"]',
    )

    settings = Settings()

    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_cors_origins_accepts_comma_separated_string(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:5173, http://127.0.0.1:5173",
    )

    settings = Settings()

    assert settings.CORS_ORIGINS == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
