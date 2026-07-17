"""Domain events for the Finding Event Stream (§2.14 / §3.1).

Normative stream types: FindingCreated, DispositionChanged, FindingClosed.

These are *persisted stream* event types. Catalog design triggers
(Opened, AcknowledgementAccepted, DismissalDeclared, …) map onto
DispositionChanged edges (or FindingCreated / FindingClosed) as documented
in docs/state-machine/README.md and FindingLifecycle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class FindingCreated(DomainEvent):
    """Finding born from inspection Report (Fail | Partial | NeedsReview)."""

    event_type: ClassVar[str] = "FindingCreated"
    finding_id: str
    lineage_id: str
    control_id: str
    inspection_id: str
    fsm_state: str
    severity: str
    outcome: str
    confidence: float
    evidence: str
    reasoning: str
    actor: str


@dataclass(frozen=True, kw_only=True)
class DispositionChanged(DomainEvent):
    """Successful FSM edge (human or system)."""

    event_type: ClassVar[str] = "DispositionChanged"
    finding_id: str
    previous_disposition: str
    new_disposition: str
    previous_fsm_state: str
    new_fsm_state: str
    actor: str
    reason: str | None = None


@dataclass(frozen=True, kw_only=True)
class FindingClosed(DomainEvent):
    """System-only close from Verified or Waived."""

    event_type: ClassVar[str] = "FindingClosed"
    finding_id: str
    final_disposition: str
    final_fsm_state: str
    actor: str
    closure_reason: str | None = None
