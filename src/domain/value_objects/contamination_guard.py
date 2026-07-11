"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField


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
    allowed_machine_references: tuple[str, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_constraints: str = Field(
        min_length=1,
        description="Constraints on schema metadata in policy",
    )
