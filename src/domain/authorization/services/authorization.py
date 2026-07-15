"""Capability Authorization engine — Request → matrix → SoD → allow|deny.

Reference: docs/state-machine/selma_authorization.puml, SPEC §3.2 / §3.2.1
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from domain.authorization.enums import Role
from domain.authorization.exceptions import CapabilityDeniedError
from domain.authorization.matrix import COMMAND_CAPABILITY, ROLE_CAPABILITIES, SOD_ACTIONS


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

    def capability_for_action(self, action: str) -> str:
        """Map command/action to matrix capability row."""
        if action not in COMMAND_CAPABILITY:
            raise CapabilityDeniedError(
                actor="unknown",
                capability=action,
                action=action,
                reason=f"unknown action {action!r} (no capability binding)",
            )
        return COMMAND_CAPABILITY[action]

    def capabilities_for(self, role: Role) -> frozenset[str]:
        """Return the §3.2 capability set for a role."""
        return ROLE_CAPABILITIES[role]

    def evaluate(
        self,
        *,
        actor: str,
        role: Role,
        action: str,
        creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        evidence_submitter: str | None = None,
    ) -> AuthzResult:
        """Evaluate matrix + SoD without raising (for pipeline tracing)."""
        try:
            self.enforce(
                actor=actor,
                role=role,
                action=action,
                creator_provenance=creator_provenance,
                evidence_submitter=evidence_submitter,
            )
        except CapabilityDeniedError as exc:
            return AuthzResult(
                decision=AuthzDecision.DENIED,
                actor=actor,
                role=role,
                action=action,
                capability=exc.capability,
                denial_audit={k: str(v) for k, v in exc.denial_audit.items()},
            )
        cap = self.capability_for_action(action)
        return AuthzResult(
            decision=AuthzDecision.ALLOWED,
            actor=actor,
            role=role,
            action=action,
            capability=cap,
        )

    def enforce(
        self,
        *,
        actor: str,
        role: Role,
        action: str,
        creator_provenance: frozenset[str] | set[str] | list[str] | None = None,
        evidence_submitter: str | None = None,
    ) -> None:
        """Allow or raise CapabilityDeniedError (no partial mutation)."""
        if not actor:
            raise CapabilityDeniedError(
                actor=actor or "",
                capability="",
                action=action,
                reason="unauthenticated",
            )
        capability = self.capability_for_action(action)
        granted = ROLE_CAPABILITIES[role]
        if capability not in granted:
            raise CapabilityDeniedError(
                actor=actor,
                capability=capability,
                action=action,
                reason=f"capability {capability!r} not granted to role {role.value!r}",
            )
        if action in SOD_ACTIONS or capability in SOD_ACTIONS:
            self._enforce_sod(
                actor=actor,
                action=action if action in SOD_ACTIONS else capability,
                creator_provenance=creator_provenance,
                evidence_submitter=evidence_submitter,
            )

    def _enforce_sod(
        self,
        *,
        actor: str,
        action: str,
        creator_provenance: frozenset[str] | set[str] | list[str] | None,
        evidence_submitter: str | None,
    ) -> None:
        if action == "finding.waive":
            prov = frozenset(creator_provenance or ())
            if actor in prov:
                raise CapabilityDeniedError(
                    actor=actor,
                    capability="finding.waive",
                    action="finding.waive",
                    reason="SoD-1: actor ∈ creator_provenance for control_id",
                )
        if action == "finding.approve_remediation":
            if evidence_submitter is not None and actor == evidence_submitter:
                raise CapabilityDeniedError(
                    actor=actor,
                    capability="finding.approve_remediation",
                    action="finding.approve_remediation",
                    reason="SoD-2: actor == evidence_submitter",
                )
