"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    prohibited_fields: frozenset[ProhibitedField] = Field(
        min_length=1,
        description="Schema fields that must not appear in policy prose",
    )
    allowed_machine_references: tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_constraints: GovernanceText = Field(
        description="Constraints on schema metadata in policy",
    )
