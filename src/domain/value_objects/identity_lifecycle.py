"""Identity Lifecycle Intent Value Objects."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from domain.base import DomainValueObject
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class IdentityLifecycleIntent(DomainValueObject):
    """Describes when to use each identity lifecycle operation."""

    SUPPORTED_OPERATIONS: ClassVar[frozenset[IdentityOperation]] = frozenset(IdentityOperation)

    revision: GovernanceText = Field(description="When to use revision")
    fork: GovernanceText = Field(description="When to use fork")
    merge: GovernanceText = Field(description="When to use merge")
    split: GovernanceText = Field(description="When to use split")
    rename: GovernanceText = Field(description="When to use rename")
    retire: GovernanceText = Field(description="When to use retire")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    def guidance_for(self, a_operation: IdentityOperation) -> GovernanceText:
        """Return authoring guidance for the given lifecycle operation."""
        return getattr(self, a_operation.value)
