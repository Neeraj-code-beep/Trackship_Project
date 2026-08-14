"""Shared application errors that are safe to expose through the API."""

from __future__ import annotations


class AppError(RuntimeError):
    """Base class for known API-facing failures."""

    def __init__(self, message: str, *, error_code: str, status_code: int) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


class RaceNotFoundError(AppError):
    def __init__(self, race_id: str) -> None:
        super().__init__(
            f"Race '{race_id}' was not found.",
            error_code="RACE_NOT_FOUND",
            status_code=404,
        )
