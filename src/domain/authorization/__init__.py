"""Capability Authorization bounded context (SPEC §3.2, selma_authorization.puml)."""

from __future__ import annotations

from domain.authorization.enums import Role
from domain.authorization.exceptions import AuthorizationError
from domain.authorization.exceptions import CapabilityDeniedError
from domain.authorization.matrix import COMMAND_CAPABILITY
from domain.authorization.matrix import ROLE_CAPABILITIES
from domain.authorization.services.authorization import AuthorizationService
from domain.authorization.services.authorization import AuthzDecision
from domain.authorization.services.authorization import AuthzResult

__all__ = [
    "COMMAND_CAPABILITY",
    "ROLE_CAPABILITIES",
    "AuthorizationError",
    "AuthorizationService",
    "AuthzDecision",
    "AuthzResult",
    "CapabilityDeniedError",
    "Role",
]
