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

from domain.authorization import AuthorizationService, Role
from domain.finding.enums import Disposition, EvaluatorOutcome, FsmState, Severity
from domain.finding.events import DispositionChanged, FindingClosed, FindingCreated
from domain.finding.exceptions import (
    InvalidFindingTransitionError,
    OptimisticConcurrencyError,
)
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
        "event_id": DomainEvent._new_id(),
        "occurred_at": DomainEvent._now_utc(),
    }


def _bump(finding: Finding, **updates: object) -> Finding:
    data = finding.model_dump()
    data.update(updates)
    data["version"] = finding.version + 1
    return Finding.model_validate(data)


class FindingLifecycle:
    """Pure Finding FSM engine with AuthorizationService gates."""

    def __init__(self, authz: AuthorizationService | None = None) -> None:
        self._authz = authz or AuthorizationService()

    def create_from_inspection(
        self,
        *,
        lineage_id: str,
        control_id: str,
        inspection_id: str,
        outcome: EvaluatorOutcome | str,
        severity: Severity | str = Severity.MEDIUM,
        confidence: float = 1.0,
        evidence: str = "",
        reasoning: str = "",
        finding_id: str | None = None,
    ) -> TransitionResult:
        """Birth finding (FindingCreated) then system Opened auto-transition."""
        outcome_s = outcome if isinstance(outcome, str) else outcome.value
        if outcome_s not in {
            EvaluatorOutcome.FAIL.value,
            EvaluatorOutcome.PARTIAL.value,
            EvaluatorOutcome.NEEDS_REVIEW.value,
        }:
            raise InvalidFindingTransitionError(
                f"Outcome {outcome_s!r} does not birth a finding (Pass produces none)"
            )
        fid = finding_id or str(uuid4())
        created = Finding(
            finding_id=fid,
            lineage_id=lineage_id,
            control_id=control_id,
            inspection_id=inspection_id,
            fsm_state=FsmState.CREATED,
            disposition=Disposition.VALID,
            severity=Severity(severity) if not isinstance(severity, Severity) else severity,
            outcome=outcome_s,
            confidence=confidence,
            evidence=evidence,
            reasoning=reasoning,
            actor=SYSTEM_ACTOR,
            version=0,
        )
        created_ev = FindingCreated(
            **_meta(),
            finding_id=fid,
            lineage_id=lineage_id,
            control_id=control_id,
            inspection_id=inspection_id,
            fsm_state=FsmState.CREATED.value,
            severity=created.severity.value,
            outcome=outcome_s,
            confidence=confidence,
            evidence=evidence,
            reasoning=reasoning,
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
        finding: Finding,
        *,
        actor: str,
        role: Role = Role.COMPLIANCE_REPRESENTATIVE,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
    ) -> TransitionResult:
        """Open → Acknowledged (design: AcknowledgementAccepted)."""
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.OPEN)
        self._enforce(actor, role, "finding.acknowledge", role_capabilities)
        nxt = _bump(finding, fsm_state=FsmState.ACKNOWLEDGED, actor=actor)
        return TransitionResult(finding=nxt, events=(self._disp(finding, nxt, actor),))

    def dismiss(
        self,
        finding: Finding,
        *,
        actor: str,
        role: Role = Role.REGULATORY_OFFICIAL,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
        reason: str | None = None,
    ) -> TransitionResult:
        """Open → Dismissed terminal (design: DismissalDeclared)."""
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.OPEN)
        self._enforce(actor, role, "finding.dismiss", role_capabilities)
        nxt = _bump(
            finding,
            fsm_state=FsmState.DISMISSED,
            disposition=Disposition.INVALID,
            actor=actor,
        )
        return TransitionResult(finding=nxt, events=(self._disp(finding, nxt, actor, reason),))

    def waive(
        self,
        finding: Finding,
        *,
        actor: str,
        creator_provenance: frozenset[str] | set[str] | list[str],
        role: Role = Role.REGULATORY_OFFICIAL,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
        reason: str | None = None,
    ) -> TransitionResult:
        """Open → Waived → Closed; SoD-1 (design: WaiverGranted + FindingClosed)."""
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.OPEN)
        self._enforce(
            actor,
            role,
            "finding.waive",
            role_capabilities,
            creator_provenance=creator_provenance,
        )
        waived = _bump(
            finding,
            fsm_state=FsmState.WAIVED,
            disposition=Disposition.WAIVED,
            actor=actor,
        )
        waive_ev = self._disp(finding, waived, actor, reason)
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
        finding: Finding,
        *,
        actor: str,
        role: Role = Role.COMPLIANCE_REPRESENTATIVE,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
        reason: str | None = None,
    ) -> TransitionResult:
        """Acknowledged → Evidence Submitted → Pending Verification.

        Design: EvidenceAccepted then system VerificationRequested.
        """
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.ACKNOWLEDGED)
        self._enforce(actor, role, "evidence.submit", role_capabilities)
        submitted = _bump(
            finding,
            fsm_state=FsmState.EVIDENCE_SUBMITTED,
            evidence_submitter=actor,
            actor=actor,
        )
        sub_ev = self._disp(finding, submitted, actor, reason)
        pending = _bump(
            submitted,
            fsm_state=FsmState.PENDING_VERIFICATION,
            actor=SYSTEM_ACTOR,
        )
        pend_ev = self._disp(submitted, pending, SYSTEM_ACTOR, "system on evidence receipt")
        return TransitionResult(finding=pending, events=(sub_ev, pend_ev))

    def approve_remediation(
        self,
        finding: Finding,
        *,
        actor: str,
        role: Role = Role.REGULATORY_OFFICIAL,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
        reason: str | None = None,
    ) -> TransitionResult:
        """Pending Verification → Verified → Closed; SoD-2.

        Design: RemediationApproved then system FindingClosed.
        """
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.PENDING_VERIFICATION)
        self._enforce(
            actor,
            role,
            "finding.approve_remediation",
            role_capabilities,
            evidence_submitter=finding.evidence_submitter,
        )
        verified = _bump(finding, fsm_state=FsmState.VERIFIED, actor=actor)
        ver_ev = self._disp(finding, verified, actor, reason)
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
        finding: Finding,
        *,
        actor: str,
        role: Role = Role.REGULATORY_OFFICIAL,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
        reason: str | None = None,
    ) -> TransitionResult:
        """Pending Verification → Rejected (design: RemediationRejected)."""
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.PENDING_VERIFICATION)
        self._enforce(actor, role, "finding.reject_remediation", role_capabilities)
        nxt = _bump(finding, fsm_state=FsmState.REJECTED, actor=actor)
        return TransitionResult(finding=nxt, events=(self._disp(finding, nxt, actor, reason),))

    def reopen(
        self,
        finding: Finding,
        *,
        actor: str,
        comments: str,
        role: Role = Role.REGULATORY_OFFICIAL,
        role_capabilities: frozenset[str] | None = None,
        expected_version: int | None = None,
    ) -> TransitionResult:
        """Rejected → Open; capability finding.reject_remediation (S-14c).

        Design: ReopenDeclared.
        """
        self._guard_version(finding, expected_version)
        self._require_state(finding, FsmState.REJECTED)
        if not comments or not comments.strip():
            raise InvalidFindingTransitionError("finding.reopen requires mandatory comments")
        self._enforce(actor, role, "finding.reopen", role_capabilities)
        nxt = _bump(finding, fsm_state=FsmState.OPEN, actor=actor)
        return TransitionResult(
            finding=nxt,
            events=(self._disp(finding, nxt, actor, comments.strip()),),
        )

    def human_close_forbidden(self, finding: Finding, *, actor: str) -> None:
        """Explicit guard: humans never close findings."""
        raise InvalidFindingTransitionError(
            f"Human actor {actor!r} cannot close finding {finding.finding_id!r}; "
            "only System after Verified or Waived"
        )

    def _enforce(
        self,
        actor: str,
        role: Role,
        action: str,
        role_capabilities: frozenset[str] | None,
        *,
        creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        evidence_submitter: str | None = None,
    ) -> None:
        if role_capabilities is not None:
            # Test/legacy path: override matrix with explicit capability set.
            capability = self._authz.capability_for_action(action)
            if capability not in role_capabilities:
                from domain.authorization import CapabilityDeniedError

                raise CapabilityDeniedError(
                    actor=actor,
                    capability=capability,
                    action=action,
                    reason=f"capability {capability!r} not granted to actor role",
                )
            # Still apply SoD via authz when action is SoD-relevant
            if action in {"finding.waive", "finding.approve_remediation"} or capability in {
                "finding.waive",
                "finding.approve_remediation",
            }:
                self._authz._enforce_sod(
                    actor=actor,
                    action=capability if capability in {"finding.waive", "finding.approve_remediation"} else action,
                    creator_provenance=creator_provenance,
                    evidence_submitter=evidence_submitter,
                )
            return
        self._authz.enforce(
            actor=actor,
            role=role,
            action=action,
            creator_provenance=creator_provenance,
            evidence_submitter=evidence_submitter,
        )

    def _require_state(self, finding: Finding, expected: FsmState) -> None:
        if finding.fsm_state != expected:
            raise InvalidFindingTransitionError(
                f"Illegal transition from {finding.fsm_state.value!r}; expected {expected.value!r}"
            )

    def _guard_version(self, finding: Finding, expected_version: int | None) -> None:
        if expected_version is not None and expected_version != finding.version:
            raise OptimisticConcurrencyError(
                finding.finding_id,
                expected_version,
                finding.version,
            )

    def _disp(
        self,
        before: Finding,
        after: Finding,
        actor: str,
        reason: str | None = None,
    ) -> DispositionChanged:
        return DispositionChanged(
            **_meta(),
            finding_id=after.finding_id,
            previous_disposition=before.disposition.value,
            new_disposition=after.disposition.value,
            previous_fsm_state=before.fsm_state.value,
            new_fsm_state=after.fsm_state.value,
            actor=actor,
            reason=reason,
        )
