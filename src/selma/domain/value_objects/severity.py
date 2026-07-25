"""Severity value object — severity level for findings.

Immutable enum-like value object.
"""

from __future__ import annotations

from enum import StrEnum


class Severity(StrEnum):
    """Severity level for findings. Value object."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"
