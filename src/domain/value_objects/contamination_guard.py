"""Contamination guard value object."""

from __future__ import annotations

from typing import FrozenSet, Tuple

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: FrozenSet[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: Tuple[str, ...] = Field(description="How Machine IDs may appear in policy")
    metadata_note: str = Field(description="Constraints on schema metadata in policy")
