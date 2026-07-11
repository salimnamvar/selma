"""Writing principles — authoring guidance entries (policy_doctrine.yaml: writing_principles)."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class WritingPrinciple(BaseModel):
    """One entry in the policy_doctrine.yaml ``writing_principles`` collection."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str = Field(
        pattern=r"^WP-\d{3}$",
        description="Unique principle identifier",
    )
    title: str = Field(min_length=1, description="Short principle name")
    description: str = Field(min_length=1, description="Detailed guidance")
