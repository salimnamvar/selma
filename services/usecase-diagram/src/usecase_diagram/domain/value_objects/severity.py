"""Severity value object for violation classification."""

from enum import StrEnum


class Severity(StrEnum):
    """Violation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
