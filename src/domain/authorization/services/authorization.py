"""Capability Authorization engine — Request → matrix → SoD → allow|deny.

Reference: docs/state-machine/selma_authorization.puml, SPEC §3.2 / §3.2.1

Design events (past-tense triggers on the catalog FSM): AuthzRequestReceived,
AuthzIdentityVerified, AuthzCapabilityChecked, AuthzSoDRequired / Skipped /
Passed, AuthzAllowed / AuthzDispatched, AuthzDenied, AuthzDenialAudited,
AuthzDomainUnchanged. Unhandled-event policy: reject.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from domain.authorization.exceptions import CapabilityDeniedError
from domain.authorization.matrix import COMMAND_CAPABILITY
from domain.authorization.matrix import ROLE_CAPABILITIES
from domain.authorization.matrix import SOD_ACTIONS

if TYPE_CHECKING:
    from domain.authorization.enums import Role


class AuthzDecision(StrEnum):
    """Terminal outcome of an authorization evaluation."""

    ALLOWED = "allowed"
    DENIED = "denied"


@dataclass(frozen=True)
class AuthzResult:
    """Result of enforce / evaluate (success path is ALLOWED only via return)."""

    decision: AuthzDecision
    actor: str
    role: Role
    action: str
    capability: str
    denial_audit: dict[str, str] | None = None


class AuthorizationService:
    """Cross-cutting capability + SoD gate (hard-reject semantics)."""

    def capability_for_action(self, a_action: str) -> str:
        """Map command/action to matrix capability row."""
        if a_action not in COMMAND_CAPABILITY:
            raise CapabilityDeniedError(
                actor="unknown",
                capability=a_action,
                action=a_action,
                reason=f"unknown action {a_action!r} (no capability binding)",
            )
        return COMMAND_CAPABILITY[a_action]

    def capabilities_for(self, a_role: Role) -> frozenset[str]:
        """Return the §3.2 capability set for a role."""
        return ROLE_CAPABILITIES[a_role]

    def evaluate(
        self,
        *,
        a_actor: str,
        a_role: Role,
        a_action: str,
        a_creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        a_evidence_submitter: str | None = None,
    ) -> AuthzResult:
        """Evaluate matrix + SoD without raising (for pipeline tracing)."""
        result: AuthzResult
        try:
            self.enforce(
                a_actor=a_actor,
                a_role=a_role,
                a_action=a_action,
                a_creator_provenance=a_creator_provenance,
                a_evidence_submitter=a_evidence_submitter,
            )
            cap = self.capability_for_action(a_action)
            result = AuthzResult(
                decision=AuthzDecision.ALLOWED,
                actor=a_actor,
                role=a_role,
                action=a_action,
                capability=cap,
            )
        except CapabilityDeniedError as exc:
            result = AuthzResult(
                decision=AuthzDecision.DENIED,
                actor=a_actor,
                role=a_role,
                action=a_action,
                capability=exc.capability,
                denial_audit={k: str(v) for k, v in exc.denial_audit.items()},
            )
        return result

    def enforce(
        self,
        *,
        a_actor: str,
        a_role: Role,
        a_action: str,
        a_creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        a_evidence_submitter: str | None = None,
    ) -> None:
        """Allow or raise CapabilityDeniedError (no partial mutation)."""
        if not a_actor:
            raise CapabilityDeniedError(
                actor=a_actor or "",
                capability="",
                action=a_action,
                reason="unauthenticated",
            )
        capability = self.capability_for_action(a_action)
        granted = ROLE_CAPABILITIES[a_role]
        if capability not in granted:
            raise CapabilityDeniedError(
                actor=a_actor,
                capability=capability,
                action=a_action,
                reason=f"capability {capability!r} not granted to role {a_role.value!r}",
            )
        if a_action in SOD_ACTIONS or capability in SOD_ACTIONS:
            self._enforce_sod(
                a_actor=a_actor,
                a_action=a_action if a_action in SOD_ACTIONS else capability,
                a_creator_provenance=a_creator_provenance,
                a_evidence_submitter=a_evidence_submitter,
            )

    def _enforce_sod(
        self,
        *,
        a_actor: str,
        a_action: str,
        a_creator_provenance: frozenset[str] | set[str] | list[str] | None,
        a_evidence_submitter: str | None,
    ) -> None:
        if a_action == "finding.waive":
            prov = frozenset(a_creator_provenance or ())
            if a_actor in prov:
                raise CapabilityDeniedError(
                    actor=a_actor,
                    capability="finding.waive",
                    action="finding.waive",
                    reason="SoD-1: actor ∈ creator_provenance for control_id",
                )
        if (
            a_action == "finding.approve_remediation"
            and a_evidence_submitter is not None
            and a_actor == a_evidence_submitter
        ):
            raise CapabilityDeniedError(
                actor=a_actor,
                capability="finding.approve_remediation",
                action="finding.approve_remediation",
                reason="SoD-2: actor == evidence_submitter",
            )
