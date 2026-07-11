"""Lifecycle Definition Value Objects."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from domain.base import EnumGuidedVO
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class LifecycleDefinition(EnumGuidedVO):
    """Describes when to use each identity lifecycle operation."""

    _GUIDANCE_ENUM: ClassVar[type[IdentityOperation]] = IdentityOperation

    revision: GovernanceText = Field(description="When to use revision")
    fork: GovernanceText = Field(description="When to use fork")
    merge: GovernanceText = Field(description="When to use merge")
    split: GovernanceText = Field(description="When to use split")
    rename: GovernanceText = Field(description="When to use rename")
    retire: GovernanceText = Field(description="When to use retire")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")
