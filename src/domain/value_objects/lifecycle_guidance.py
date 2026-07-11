"""Lifecycle guidance — flat YAML-shaped intent for identity operations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class LifecycleGuidance(BaseModel):
    """Direct mapping of identity lifecycle intent (YAML field names)."""

    model_config = VO_CONFIG

    revision: GovernanceText = Field(description="When to use revision")
    fork: GovernanceText = Field(description="When to use fork")
    merge: GovernanceText = Field(description="When to use merge")
    split: GovernanceText = Field(description="When to use split")
    rename: GovernanceText = Field(description="When to use rename")
    retire: GovernanceText = Field(description="When to use retire")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    def get_guidance(self, operation: IdentityOperation) -> str:
        """Return guidance text for the given operation."""
        return getattr(self, operation.value)