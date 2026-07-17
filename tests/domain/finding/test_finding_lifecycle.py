"""Tests for FindingLifecycle — aligned to §3.1 FSM and FINDING_FSM_TEST_SCENARIOS.md."""

from __future__ import annotations

import pytest

from domain.finding import (
    COMPLIANCE_CAPS,
    OFFICIAL_CAPS,
    CapabilityDeniedError,
    EvaluatorOutcome,
    FindingClosed,
    FindingCreated,
    FindingLifecycle,
    FsmState,
    InvalidFindingTransitionError,
    OptimisticConcurrencyError,
    Severity,
)


@pytest.fixture
def lc() -> FindingLifecycle:
    return FindingLifecycle()


def _open(lc: FindingLifecycle):
    return lc.create_from_inspection(
        lineage_id="RULE-001",
        control_id="RULE-001",
        inspection_id="insp-1",
        outcome=EvaluatorOutcome.FAIL,
        severity=Severity.HIGH,
    )


@pytest.mark.unit
@pytest.mark.domain
class TestBirth:
    def test_fail_births_and_auto_opens(self, lc: FindingLifecycle) -> None:
        result = _open(lc)
        assert result.finding.fsm_state == FsmState.OPEN
        assert isinstance(result.events[0], FindingCreated)
        assert result.events[0].fsm_state == FsmState.CREATED.value
        assert result.finding.version == 1

    def test_pass_does_not_birth(self, lc: FindingLifecycle) -> None:
        with pytest.raises(InvalidFindingTransitionError):
            lc.create_from_inspection(
                lineage_id="RULE-001",
                control_id="RULE-001",
                inspection_id="insp-1",
                outcome="Pass",
            )


@pytest.mark.unit
@pytest.mark.domain
class TestOpenHub:
    def test_acknowledge(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        result = lc.acknowledge(
            opened,
            actor="cr-1",
            role_capabilities=COMPLIANCE_CAPS,
            expected_version=opened.version,
        )
        assert result.finding.fsm_state == FsmState.ACKNOWLEDGED

    def test_dismiss_terminal(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        result = lc.dismiss(
            opened,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
        )
        assert result.finding.fsm_state == FsmState.DISMISSED
        assert result.finding.is_terminal

    def test_waive_sod1_pass_auto_closes(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        result = lc.waive(
            opened,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
            creator_provenance=frozenset({"author-other"}),
        )
        assert result.finding.fsm_state == FsmState.CLOSED
        assert any(isinstance(e, FindingClosed) for e in result.events)

    def test_waive_sod1_deny(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        with pytest.raises(CapabilityDeniedError) as exc:
            lc.waive(
                opened,
                actor="author-1",
                role_capabilities=OFFICIAL_CAPS,
                creator_provenance=frozenset({"author-1"}),
            )
        assert exc.value.denial_audit["outcome"] == "denied"
        assert opened.fsm_state == FsmState.OPEN


@pytest.mark.unit
@pytest.mark.domain
class TestRemediation:
    def _pending(self, lc: FindingLifecycle):
        opened = _open(lc).finding
        acked = lc.acknowledge(opened, actor="cr-1", role_capabilities=COMPLIANCE_CAPS).finding
        return lc.submit_evidence(
            acked,
            actor="cr-1",
            role_capabilities=COMPLIANCE_CAPS,
        ).finding

    def test_evidence_to_pending(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        assert pending.fsm_state == FsmState.PENDING_VERIFICATION
        assert pending.evidence_submitter == "cr-1"

    def test_approve_sod2_pass_auto_closes(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        result = lc.approve_remediation(
            pending,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
        )
        assert result.finding.fsm_state == FsmState.CLOSED
        assert any(isinstance(e, FindingClosed) for e in result.events)

    def test_approve_sod2_deny(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        # give compliance actor approve? still SoD-2 if same submitter —
        # Official who is also submitter: use submitter with OFFICIAL_CAPS
        with pytest.raises(CapabilityDeniedError) as exc:
            lc.approve_remediation(
                pending,
                actor="cr-1",
                role_capabilities=OFFICIAL_CAPS | COMPLIANCE_CAPS,
            )
        assert "SoD-2" in exc.value.reason

    def test_reject_then_reopen(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        rejected = lc.reject_remediation(
            pending,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
        ).finding
        assert rejected.fsm_state == FsmState.REJECTED
        reopened = lc.reopen(
            rejected,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
            comments="needs more work on evidence package",
        ).finding
        assert reopened.fsm_state == FsmState.OPEN

    def test_reopen_requires_comments(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        rejected = lc.reject_remediation(
            pending,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
        ).finding
        with pytest.raises(InvalidFindingTransitionError):
            lc.reopen(
                rejected,
                actor="ro-1",
                role_capabilities=OFFICIAL_CAPS,
                comments="   ",
            )

    def test_compliance_cannot_reopen(self, lc: FindingLifecycle) -> None:
        pending = self._pending(lc)
        rejected = lc.reject_remediation(
            pending,
            actor="ro-1",
            role_capabilities=OFFICIAL_CAPS,
        ).finding
        with pytest.raises(CapabilityDeniedError):
            lc.reopen(
                rejected,
                actor="cr-1",
                role_capabilities=COMPLIANCE_CAPS,
                comments="please reopen",
            )


@pytest.mark.unit
@pytest.mark.domain
class TestConcurrencyAndForbidden:
    def test_stale_version_409(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        with pytest.raises(OptimisticConcurrencyError):
            lc.acknowledge(
                opened,
                actor="cr-1",
                role_capabilities=COMPLIANCE_CAPS,
                expected_version=opened.version - 1 if opened.version else -1,
            )

    def test_human_close_forbidden(self, lc: FindingLifecycle) -> None:
        opened = _open(lc).finding
        with pytest.raises(InvalidFindingTransitionError):
            lc.human_close_forbidden(opened, actor="ro-1")

    def test_capability_matrix_deny_acknowledge_for_official_only_role(self, lc: FindingLifecycle) -> None:
        # Official lacks finding.acknowledge in OFFICIAL_CAPS
        opened = _open(lc).finding
        with pytest.raises(CapabilityDeniedError):
            lc.acknowledge(
                opened,
                actor="ro-1",
                role_capabilities=OFFICIAL_CAPS,
            )
