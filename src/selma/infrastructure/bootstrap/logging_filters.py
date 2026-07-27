"""Logging filters for structured context."""

from __future__ import annotations

import logging
import secrets


class RunContextFilter(logging.Filter):
    """Adds run_id to all log records for correlation."""

    def __init__(self) -> None:
        super().__init__()
        self.run_id: str = secrets.token_hex(4)

    def filter(self, record: logging.LogRecord) -> bool:
        record.__dict__["run_id"] = self.run_id
        return True
