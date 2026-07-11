"""Writing principles — authoring guidance entries (policy_doctrine.yaml: writing_principles)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.identifiers import GovernanceText


class WritingPrinciple(BaseModel):
    """One entry in the policy_doctrine.yaml ``writing_principles`` collection."""

    model_config = VO_CONFIG

    id: str = Field(
        pattern=r"^WP-\d{3}$",
        description="Unique principle identifier",
    )
    title: GovernanceText = Field(description="Short principle name")
    description: GovernanceText = Field(description="Detailed guidance")