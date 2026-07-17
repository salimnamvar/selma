"""Inspection pipeline status and fault taxonomy (§3.3 / §3.6)."""

from __future__ import annotations

from enum import StrEnum


class InspectionStatus(StrEnum):
    """Terminal inspection run status."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    REJECTED_INGRESS = "rejected_ingress"


class FaultType(StrEnum):
    """Typed fault taxonomy (§3.3)."""

    DETERMINISTIC = "Deterministic"
    PARTIAL = "Partial"
    AMBIGUOUS = "Ambiguous"
    DEPENDENCY = "Dependency"
    TIMEOUT = "Timeout"
    RESOURCE = "Resource"
    SCHEMA = "Schema"
    CORRUPTION = "Corruption"
