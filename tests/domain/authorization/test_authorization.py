"""Tests for AuthorizationService — matrix + SoD + command bindings."""

from __future__ import annotations

import pytest

from domain.authorization import (
    AuthorizationService,
    AuthzDecision,
    CapabilityDeniedError,
    Role,
)


@pytest.fixture
def authz() -> AuthorizationService:
    return AuthorizationService()


@pytest.mark.unit
@pytest.mark.domain
class TestMatrix:
    def test_official_can_waive(self, authz: AuthorizationService) -> None:
        authz.enforce(
            actor="ro-1",
            role=Role.REGULATORY_OFFICIAL,
            action="finding.waive",
            creator_provenance=frozenset({"other"}),
        )

    def test_compliance_cannot_waive(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError):
            authz.enforce(
                actor="cr-1",
                role=Role.COMPLIANCE_REPRESENTATIVE,
                action="finding.waive",
                creator_provenance=frozenset(),
            )

    def test_split_gated_by_fork(self, authz: AuthorizationService) -> None:
        assert authz.capability_for_action("directive.split") == "directive.fork"
        authz.enforce(
            actor="ro-1",
            role=Role.REGULATORY_OFFICIAL,
            action="directive.split",
        )

    def test_reopen_gated_by_reject(self, authz: AuthorizationService) -> None:
        assert authz.capability_for_action("finding.reopen") == "finding.reject_remediation"
        authz.enforce(
            actor="ro-1",
            role=Role.REGULATORY_OFFICIAL,
            action="finding.reopen",
        )

    def test_system_can_submit_inspection(self, authz: AuthorizationService) -> None:
        authz.enforce(
            actor="svc",
            role=Role.SYSTEM,
            action="inspection.submit",
        )


@pytest.mark.unit
@pytest.mark.domain
class TestSoD:
    def test_sod1_deny(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError) as exc:
            authz.enforce(
                actor="author",
                role=Role.REGULATORY_OFFICIAL,
                action="finding.waive",
                creator_provenance=frozenset({"author"}),
            )
        assert "SoD-1" in exc.value.reason
        assert exc.value.denial_audit["outcome"] == "denied"

    def test_sod2_deny(self, authz: AuthorizationService) -> None:
        with pytest.raises(CapabilityDeniedError) as exc:
            authz.enforce(
                actor="cr-1",
                role=Role.REGULATORY_OFFICIAL,
                action="finding.approve_remediation",
                evidence_submitter="cr-1",
            )
        assert "SoD-2" in exc.value.reason

    def test_evaluate_denied_returns_audit(self, authz: AuthorizationService) -> None:
        result = authz.evaluate(
            actor="cr-1",
            role=Role.COMPLIANCE_REPRESENTATIVE,
            action="finding.dismiss",
        )
        assert result.decision == AuthzDecision.DENIED
        assert result.denial_audit is not None
