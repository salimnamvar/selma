"""Enumerations for the Finding Lifecycle bounded context.

Reference: SPECIFICATION.md §3.1, docs/state-machine/selma_finding_lifecycle.puml
"""

from __future__ import annotations

from enum import StrEnum


class FsmState(StrEnum):
    """Normative Finding FSM states (§3.1)."""

    CREATED = "Created"
    OPEN = "Open"
    ACKNOWLEDGED = "Acknowledged"
    EVIDENCE_SUBMITTED = "Evidence Submitted"
    PENDING_VERIFICATION = "Pending Verification"
    VERIFIED = "Verified"
    REJECTED = "Rejected"
    DISMISSED = "Dismissed"
    WAIVED = "Waived"
    CLOSED = "Closed"


class Disposition(StrEnum):
    """Finding disposition values (§3.1)."""

    VALID = "valid"
    INVALID = "invalid"
    WAIVED = "waived"


class EvaluatorOutcome(StrEnum):
    """Evaluator outcomes that may birth a finding (§2.9 / §3.1)."""

    FAIL = "Fail"
    PARTIAL = "Partial"
    NEEDS_REVIEW = "NeedsReview"


class Severity(StrEnum):
    """Finding severity classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"
