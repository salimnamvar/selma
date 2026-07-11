"""Identity Lifecycle Intent Value Objects.

When to use each identity lifecycle operation. Field names match the YAML
document and the IdentityOperation enum values so Pydantic validates
completeness without a custom before-validator reshape.
"""

from __future__ import annotations

from typing import FrozenSet

from pydantic import Field

from domain.base import DomainValueObject
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class IdentityLifecycleIntent(DomainValueObject):
    """Describes when to use each identity lifecycle operation.

    Attributes:
        revision (GovernanceText): When to use revision.
        fork (GovernanceText): When to use fork.
        merge (GovernanceText): When to use merge.
        split (GovernanceText): When to use split.
        rename (GovernanceText): When to use rename.
        retire (GovernanceText): When to use retire.
        dag_intent (GovernanceText): Constraint on lineage ancestry graph structure.
    """

    revision: GovernanceText = Field(description="When to use revision")
    fork: GovernanceText = Field(description="When to use fork")
    merge: GovernanceText = Field(description="When to use merge")
    split: GovernanceText = Field(description="When to use split")
    rename: GovernanceText = Field(description="When to use rename")
    retire: GovernanceText = Field(description="When to use retire")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    def guidance_for(self, a_operation: IdentityOperation) -> GovernanceText:
        """Return authoring guidance for the given lifecycle operation.

        Args:
            a_operation (IdentityOperation): Lifecycle operation.

        Returns:
            GovernanceText: Guidance text for the operation.
        """
        result: GovernanceText = getattr(self, a_operation.value)
        return result

    def supported_operations(self) -> FrozenSet[IdentityOperation]:
        """Return the set of operations covered by this intent.

        Returns:
            FrozenSet[IdentityOperation]: Supported operations.
        """
        result: FrozenSet[IdentityOperation] = frozenset(IdentityOperation)
        return result
