"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel
from pydantic import Field

from pydantic import ConfigDict
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
    metadata_constraints: GovernanceText = Field(description="Constraints on schema metadata in policy")

    def is_prohibited(self, field: str | ProhibitedField) -> bool:
        """Return True when ``field`` is listed in ``prohibited_fields``."""
        try:
            prohibited_field = field if isinstance(field, ProhibitedField) else ProhibitedField(field)
        except ValueError:
            return False
        return prohibited_field in self.prohibited_fields

    def validate(self, fields: Iterable[str]) -> None:
        """Raise ValueError when any ``fields`` appear in ``prohibited_fields``."""
        violations = [field for field in fields if self.is_prohibited(field)]
        if violations:
            raise ValueError(f"Prohibited fields: {violations}")
