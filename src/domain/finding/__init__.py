"""Finding Lifecycle bounded context (normative SPEC §3.1).

Implements the canonical state machine in
``docs/state-machine/selma_finding_lifecycle.puml``.
"""

from __future__ import annotations

from domain.finding.enums import Disposition, EvaluatorOutcome, FsmState, Severity
from domain.finding.events import DispositionChanged, FindingClosed, FindingCreated
from domain.finding.exceptions import (
    CapabilityDeniedError,
    FindingDomainError,
    InvalidFindingTransitionError,
    OptimisticConcurrencyError,
)
from domain.finding.finding import Finding
from domain.finding.services.finding_lifecycle import (
    COMPLIANCE_CAPS,
    OFFICIAL_CAPS,
    SYSTEM_CAPS,
    FindingLifecycle,
    TransitionResult,
)

__all__ = [
    "COMPLIANCE_CAPS",
    "OFFICIAL_CAPS",
    "SYSTEM_CAPS",
    "CapabilityDeniedError",
    "Disposition",
    "DispositionChanged",
    "EvaluatorOutcome",
    "Finding",
    "FindingClosed",
    "FindingCreated",
    "FindingDomainError",
    "FindingLifecycle",
    "FsmState",
    "InvalidFindingTransitionError",
    "OptimisticConcurrencyError",
    "Severity",
    "TransitionResult",
]
