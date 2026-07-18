"""Finding Lifecycle bounded context (normative SPEC §3.1).

Implements the canonical state machine in
``docs/state-machine/selma_finding_lifecycle.puml``.

Public methods are *commands*; diagram edges use past-tense *design events*
(STM-032). Stream types remain FindingCreated / DispositionChanged /
FindingClosed (§2.14). See ``FindingLifecycle`` module docstring for the map.
"""

from __future__ import annotations

from domain.finding.enums import Disposition
from domain.finding.enums import EvaluatorOutcome
from domain.finding.enums import FsmState
from domain.finding.enums import Severity
from domain.finding.events import DispositionChanged
from domain.finding.events import FindingClosed
from domain.finding.events import FindingCreated
from domain.finding.exceptions import CapabilityDeniedError
from domain.finding.exceptions import FindingDomainError
from domain.finding.exceptions import InvalidFindingTransitionError
from domain.finding.exceptions import OptimisticConcurrencyError
from domain.finding.finding import Finding
from domain.finding.services.finding_lifecycle import COMPLIANCE_CAPS
from domain.finding.services.finding_lifecycle import OFFICIAL_CAPS
from domain.finding.services.finding_lifecycle import SYSTEM_CAPS
from domain.finding.services.finding_lifecycle import FindingLifecycle
from domain.finding.services.finding_lifecycle import TransitionResult

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
