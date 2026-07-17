"""Authorization domain exceptions."""

from __future__ import annotations

from typing import Any


class AuthorizationError(Exception):
    """Base authorization error."""


class CapabilityDeniedError(AuthorizationError):
    """Hard deny: no domain mutation; emit denial audit only (HTTP 403)."""

    def __init__(
        self,
        *,
        actor: str,
        capability: str,
        action: str,
        reason: str,
    ) -> None:
        self.actor = actor
        self.capability = capability
        self.action = action
        self.reason = reason
        self.denial_audit: dict[str, Any] = {
            "actor": actor,
            "capability": capability,
            "action": action,
            "outcome": "denied",
            "reason": reason,
        }
        super().__init__(f"CapabilityDenied: {action} by {actor!r} — {reason}")
