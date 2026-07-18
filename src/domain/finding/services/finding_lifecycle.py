"""Finding Lifecycle engine — normative §3.1 transitions + Authz + SoD.

Reference:
  - docs/state-machine/selma_finding_lifecycle.puml  (design triggers)
  - docs/state-machine/README.md  (design-event ↔ command matrix)
  - SPECIFICATION.md §3.1, §3.2, §2.14

Design-event vocabulary (doctrine STM-032 past-tense triggers) vs this API:

  Design event              Command / method              Stream event
  -----------------------   ---------------------------   -------------------
  FindingCreated            create_from_inspection        FindingCreated
  Opened                    (auto in create_from_inspection) DispositionChanged
  AcknowledgementAccepted   acknowledge                   DispositionChanged
  DismissalDeclared         dismiss                       DispositionChanged
  WaiverGranted             waive                         DispositionChanged
  EvidenceAccepted          submit_evidence (edge 1)      DispositionChanged
  VerificationRequested     submit_evidence (edge 2 auto) DispositionChanged
  RemediationApproved       approve_remediation           DispositionChanged
  RemediationRejected       reject_remediation            DispositionChanged
  ReopenDeclared            reopen                        DispositionChanged
  FindingClosed             system auto after verify/waive FindingClosed
  Finalized                 terminal sink (no stream)     —

Unhandled design events are rejected (STM-025 policy: reject).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from domain.authorization import AuthorizationService
from domain.authorization import CapabilityDeniedError
from domain.authorization import Role
from domain.finding.enums import Disposition
from domain.finding.enums import EvaluatorOutcome
from domain.finding.enums import FsmState
from domain.finding.enums import Severity
from domain.finding.events import DispositionChanged
from domain.finding.events import FindingClosed
from domain.finding.events import FindingCreated
from domain.finding.exceptions import InvalidFindingTransitionError
from domain.finding.exceptions import OptimisticConcurrencyError
from domain.finding.finding import Finding
from domain.shared.events import DomainEvent

SYSTEM_ACTOR = "system"

# Backward-compatible capability sets (derived from Authorization matrix).
_authz = AuthorizationService()
OFFICIAL_CAPS = _authz.capabilities_for(Role.REGULATORY_OFFICIAL)
COMPLIANCE_CAPS = _authz.capabilities_for(Role.COMPLIANCE_REPRESENTATIVE)
SYSTEM_CAPS = _authz.capabilities_for(Role.SYSTEM)


@dataclass(frozen=True)
class TransitionResult:
    """Outcome of a successful FSM transition (possibly multi-event)."""

    finding: Finding
    events: tuple[DomainEvent, ...]


def _meta() -> dict[str, str]:
    return {
        "event_id": DomainEvent.new_id(),
        "occurred_at": DomainEvent.now_utc(),
    }


def _bump(a_finding: Finding, **a_updates: object) -> Finding:
    data = a_finding.model_dump()
    data.update(a_updates)
    data["version"] = a_finding.version + 1
    return Finding.model_validate(data)


class FindingLifecycle:
    """Pure Finding FSM engine with AuthorizationService gates."""

    def __init__(self, authz: AuthorizationService | None = None) -> None:
        self._authz = authz or AuthorizationService()

    def create_from_inspection(
        self,
        *,
        a_lineage_id: str,
        a_control_id: str,
        a_inspection_id: str,
        a_outcome: EvaluatorOutcome | str,
        a_severity: Severity | str = Severity.MEDIUM,
        a_confidence: float = 1.0,
        a_evidence: str = "",
        a_reasoning: str = "",
        a_finding_id: str | None = None,
    ) -> TransitionResult:
        """Birth finding (FindingCreated) then system Opened auto-transition."""
        outcome_s = a_outcome.value if isinstance(a_outcome, EvaluatorOutcome) else a_outcome
        if outcome_s not in {
            EvaluatorOutcome.FAIL.value,
            EvaluatorOutcome.PARTIAL.value,
            EvaluatorOutcome.NEEDS_REVIEW.value,
        }:
            msg = f"Outcome {outcome_s!r} does not birth a finding (Pass produces none)"
            raise InvalidFindingTransitionError(msg)
        fid = a_finding_id or str(uuid4())
        created = Finding(
            finding_id=fid,
            lineage_id=a_lineage_id,
            control_id=a_control_id,
            inspection_id=a_inspection_id,
            fsm_state=FsmState.CREATED,
            disposition=Disposition.VALID,
            severity=Severity(a_severity) if not isinstance(a_severity, Severity) else a_severity,
            outcome=outcome_s,
            confidence=a_confidence,
            evidence=a_evidence,
            reasoning=a_reasoning,
            actor=SYSTEM_ACTOR,
            version=0,
        )
        created_ev = FindingCreated(
            **_meta(),
            finding_id=fid,
            lineage_id=a_lineage_id,
            control_id=a_control_id,
            inspection_id=a_inspection_id,
            fsm_state=FsmState.CREATED.value,
            severity=created.severity.value,
            outcome=outcome_s,
            confidence=a_confidence,
            evidence=a_evidence,
            reasoning=a_reasoning,
            actor=SYSTEM_ACTOR,
        )
        opened = _bump(created, fsm_state=FsmState.OPEN, actor=SYSTEM_ACTOR)
        open_ev = DispositionChanged(
            **_meta(),
            finding_id=fid,
            previous_disposition=Disposition.VALID.value,
            new_disposition=Disposition.VALID.value,
            previous_fsm_state=FsmState.CREATED.value,
            new_fsm_state=FsmState.OPEN.value,
            actor=SYSTEM_ACTOR,
            reason="system auto-open",
        )
        return TransitionResult(finding=opened, events=(created_ev, open_ev))

    def acknowledge(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_role: Role = Role.COMPLIANCE_REPRESENTATIVE,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
    ) -> TransitionResult:
        """Open → Acknowledged (design: AcknowledgementAccepted)."""
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.OPEN)
        self._enforce(a_actor, a_role, "finding.acknowledge", a_role_capabilities)
        nxt = _bump(a_finding, fsm_state=FsmState.ACKNOWLEDGED, actor=a_actor)
        return TransitionResult(finding=nxt, events=(self._disp(a_finding, nxt, a_actor),))

    def dismiss(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_role: Role = Role.REGULATORY_OFFICIAL,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
        a_reason: str | None = None,
    ) -> TransitionResult:
        """Open → Dismissed terminal (design: DismissalDeclared)."""
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.OPEN)
        self._enforce(a_actor, a_role, "finding.dismiss", a_role_capabilities)
        nxt = _bump(
            a_finding,
            fsm_state=FsmState.DISMISSED,
            disposition=Disposition.INVALID,
            actor=a_actor,
        )
        return TransitionResult(finding=nxt, events=(self._disp(a_finding, nxt, a_actor, a_reason),))

    def waive(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_creator_provenance: frozenset[str] | set[str] | list[str],
        a_role: Role = Role.REGULATORY_OFFICIAL,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
        a_reason: str | None = None,
    ) -> TransitionResult:
        """Open → Waived → Closed; SoD-1 (design: WaiverGranted + FindingClosed)."""
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.OPEN)
        self._enforce(
            a_actor,
            a_role,
            "finding.waive",
            a_role_capabilities,
            a_creator_provenance=a_creator_provenance,
        )
        waived = _bump(
            a_finding,
            fsm_state=FsmState.WAIVED,
            disposition=Disposition.WAIVED,
            actor=a_actor,
        )
        waive_ev = self._disp(a_finding, waived, a_actor, a_reason)
        closed = _bump(waived, fsm_state=FsmState.CLOSED, actor=SYSTEM_ACTOR)
        close_ev = FindingClosed(
            **_meta(),
            finding_id=closed.finding_id,
            final_disposition=Disposition.WAIVED.value,
            final_fsm_state=FsmState.CLOSED.value,
            actor=SYSTEM_ACTOR,
            closure_reason="system auto-close after waive",
        )
        return TransitionResult(finding=closed, events=(waive_ev, close_ev))

    def submit_evidence(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_role: Role = Role.COMPLIANCE_REPRESENTATIVE,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
        a_reason: str | None = None,
    ) -> TransitionResult:
        """Acknowledged → Evidence Submitted → Pending Verification.

        Design: EvidenceAccepted then system VerificationRequested.
        """
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.ACKNOWLEDGED)
        self._enforce(a_actor, a_role, "evidence.submit", a_role_capabilities)
        submitted = _bump(
            a_finding,
            fsm_state=FsmState.EVIDENCE_SUBMITTED,
            evidence_submitter=a_actor,
            actor=a_actor,
        )
        sub_ev = self._disp(a_finding, submitted, a_actor, a_reason)
        pending = _bump(
            submitted,
            fsm_state=FsmState.PENDING_VERIFICATION,
            actor=SYSTEM_ACTOR,
        )
        pend_ev = self._disp(submitted, pending, SYSTEM_ACTOR, "system on evidence receipt")
        return TransitionResult(finding=pending, events=(sub_ev, pend_ev))

    def approve_remediation(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_role: Role = Role.REGULATORY_OFFICIAL,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
        a_reason: str | None = None,
    ) -> TransitionResult:
        """Pending Verification → Verified → Closed; SoD-2.

        Design: RemediationApproved then system FindingClosed.
        """
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.PENDING_VERIFICATION)
        self._enforce(
            a_actor,
            a_role,
            "finding.approve_remediation",
            a_role_capabilities,
            a_evidence_submitter=a_finding.evidence_submitter,
        )
        verified = _bump(a_finding, fsm_state=FsmState.VERIFIED, actor=a_actor)
        ver_ev = self._disp(a_finding, verified, a_actor, a_reason)
        closed = _bump(verified, fsm_state=FsmState.CLOSED, actor=SYSTEM_ACTOR)
        close_ev = FindingClosed(
            **_meta(),
            finding_id=closed.finding_id,
            final_disposition=closed.disposition.value,
            final_fsm_state=FsmState.CLOSED.value,
            actor=SYSTEM_ACTOR,
            closure_reason="system auto-close after verify",
        )
        return TransitionResult(finding=closed, events=(ver_ev, close_ev))

    def reject_remediation(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_role: Role = Role.REGULATORY_OFFICIAL,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
        a_reason: str | None = None,
    ) -> TransitionResult:
        """Pending Verification → Rejected (design: RemediationRejected)."""
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.PENDING_VERIFICATION)
        self._enforce(a_actor, a_role, "finding.reject_remediation", a_role_capabilities)
        nxt = _bump(a_finding, fsm_state=FsmState.REJECTED, actor=a_actor)
        return TransitionResult(finding=nxt, events=(self._disp(a_finding, nxt, a_actor, a_reason),))

    def reopen(
        self,
        a_finding: Finding,
        *,
        a_actor: str,
        a_comments: str,
        a_role: Role = Role.REGULATORY_OFFICIAL,
        a_role_capabilities: frozenset[str] | None = None,
        a_expected_version: int | None = None,
    ) -> TransitionResult:
        """Rejected → Open; capability finding.reject_remediation (S-14c).

        Design: ReopenDeclared.
        """
        self._guard_version(a_finding, a_expected_version)
        self._require_state(a_finding, FsmState.REJECTED)
        if not a_comments or not a_comments.strip():
            msg = "finding.reopen requires mandatory comments"
            raise InvalidFindingTransitionError(msg)
        self._enforce(a_actor, a_role, "finding.reopen", a_role_capabilities)
        nxt = _bump(a_finding, fsm_state=FsmState.OPEN, actor=a_actor)
        return TransitionResult(
            finding=nxt,
            events=(self._disp(a_finding, nxt, a_actor, a_comments.strip()),),
        )

    def human_close_forbidden(self, a_finding: Finding, *, a_actor: str) -> None:
        """Explicit guard: humans never close findings."""
        msg = f"Human actor {a_actor!r} cannot close finding {a_finding.finding_id!r}; only System after Verified or Waived"
        raise InvalidFindingTransitionError(msg)

    def _enforce(
        self,
        a_actor: str,
        a_role: Role,
        a_action: str,
        a_role_capabilities: frozenset[str] | None,
        *,
        a_creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        a_evidence_submitter: str | None = None,
    ) -> None:
        if a_role_capabilities is not None:
            # Test/legacy path: override matrix with explicit capability set.
            capability = self._authz.capability_for_action(a_action)
            if capability not in a_role_capabilities:
                raise CapabilityDeniedError(
                    actor=a_actor,
                    capability=capability,
                    action=a_action,
                    reason=f"capability {capability!r} not granted to actor role",
                )
            # Still apply SoD via authz when action is SoD-relevant
            if a_action in {"finding.waive", "finding.approve_remediation"} or capability in {
                "finding.waive",
                "finding.approve_remediation",
            }:
                self._authz._enforce_sod(  # pyright: ignore[reportPrivateUsage]
                    a_actor=a_actor,
                    a_action=capability if capability in {"finding.waive", "finding.approve_remediation"} else a_action,
                    a_creator_provenance=a_creator_provenance,
                    a_evidence_submitter=a_evidence_submitter,
                )
            return
        self._authz.enforce(
            a_actor=a_actor,
            a_role=a_role,
            a_action=a_action,
            a_creator_provenance=a_creator_provenance,
            a_evidence_submitter=a_evidence_submitter,
        )

    def _require_state(self, a_finding: Finding, a_expected: FsmState) -> None:
        if a_finding.fsm_state != a_expected:
            msg = f"Illegal transition from {a_finding.fsm_state.value!r}; expected {a_expected.value!r}"
            raise InvalidFindingTransitionError(msg)

    def _guard_version(self, a_finding: Finding, a_expected_version: int | None) -> None:
        if a_expected_version is not None and a_expected_version != a_finding.version:
            raise OptimisticConcurrencyError(
                a_finding.finding_id,
                a_expected_version,
                a_finding.version,
            )

    def _disp(
        self,
        a_before: Finding,
        a_after: Finding,
        a_actor: str,
        a_reason: str | None = None,
    ) -> DispositionChanged:
        return DispositionChanged(
            **_meta(),
            finding_id=a_after.finding_id,
            previous_disposition=a_before.disposition.value,
            new_disposition=a_after.disposition.value,
            previous_fsm_state=a_before.fsm_state.value,
            new_fsm_state=a_after.fsm_state.value,
            actor=a_actor,
            reason=a_reason,
        )
