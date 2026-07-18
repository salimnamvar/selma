"""Tests for AuthorizationService — matrix + SoD + command bindings."""

from __future__ import annotations

import pytest

from domain.authorization import AuthorizationService
from domain.authorization import AuthzDecision
from domain.authorization import CapabilityDeniedError
from domain.authorization import Role


@pytest.fixture
def authz() -> AuthorizationService:
    return AuthorizationService()


@pytest.mark.unit
@pytest.mark.domain
class TestMatrix:
    def test_official_can_waive(self, authz: AuthorizationService) -> None:
        authz.enforce(
            a_actor="ro-1",
            a_role=Role.REGULATORY_OFFICIAL,
            a_action="finding.waive",
            a_creator_provenance=frozenset({"other"}),
        )

    def test_compliance_cannot_waive(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError):
            authz.enforce(
                a_actor="cr-1",
                a_role=Role.COMPLIANCE_REPRESENTATIVE,
                a_action="finding.waive",
                a_creator_provenance=frozenset(),
            )

    def test_split_gated_by_fork(self, authz: AuthorizationService) -> None:
        assert authz.capability_for_action("directive.split") == "directive.fork"
        authz.enforce(
            a_actor="ro-1",
            a_role=Role.REGULATORY_OFFICIAL,
            a_action="directive.split",
        )

    def test_reopen_gated_by_reject(self, authz: AuthorizationService) -> None:
        assert authz.capability_for_action("finding.reopen") == "finding.reject_remediation"
        authz.enforce(
            a_actor="ro-1",
            a_role=Role.REGULATORY_OFFICIAL,
            a_action="finding.reopen",
        )

    def test_system_can_submit_inspection(self, authz: AuthorizationService) -> None:
        authz.enforce(
            a_actor="svc",
            a_role=Role.SYSTEM,
            a_action="inspection.submit",
        )


@pytest.mark.unit
@pytest.mark.domain
class TestSoD:
    def test_sod1_deny(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError) as exc:
            authz.enforce(
                a_actor="author",
                a_role=Role.REGULATORY_OFFICIAL,
                a_action="finding.waive",
                a_creator_provenance=frozenset({"author"}),
            )
        assert "SoD-1" in exc.value.reason
        assert exc.value.denial_audit["outcome"] == "denied"

    def test_sod2_deny(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError) as exc:
            authz.enforce(
                a_actor="cr-1",
                a_role=Role.REGULATORY_OFFICIAL,
                a_action="finding.approve_remediation",
                a_evidence_submitter="cr-1",
            )
        assert "SoD-2" in exc.value.reason

    def test_evaluate_denied_returns_audit(self, authz: AuthorizationService) -> None:
        result = authz.evaluate(
            a_actor="cr-1",
            a_role=Role.COMPLIANCE_REPRESENTATIVE,
            a_action="finding.dismiss",
        )
        assert result.decision == AuthzDecision.DENIED
        assert result.denial_audit is not None
