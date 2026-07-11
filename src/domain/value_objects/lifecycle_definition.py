"""Lifecycle definition — flat YAML-shaped intent for identity operations."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class LifecycleDefinition(BaseModel):
    """Direct mapping of policy_doctrine.yaml ``lifecycle_definition`` field names."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    revision: GovernanceText = Field(description="When to use revision")
    fork: GovernanceText = Field(description="When to use fork")
    merge: GovernanceText = Field(description="When to use merge")
    split: GovernanceText = Field(description="When to use split")
    rename: GovernanceText = Field(description="When to use rename")
    retire: GovernanceText = Field(description="When to use retire")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    def get_lifecycle_definition(self, operation: IdentityOperation) -> str:
        """Return lifecycle text for ``operation``.

        ``IdentityOperation`` values match the flat YAML field names on this model
        (``revision``, ``fork``, ``merge``, etc.); ``dag_intent`` is not an operation.
        """
        return getattr(self, operation.value)
