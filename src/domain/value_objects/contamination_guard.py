"""Contamination Guard Value Objects."""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ContaminationGuard(DomainValueObject):
    """Defines what is prohibited and allowed in the policy layer."""

    prohibited_fields: frozenset[ProhibitedField] = Field(
        min_length=1,
        description="Schema fields that must not appear in policy prose",
    )
    allowed_machine_references: tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_note: GovernanceText = Field(description="Constraints on schema metadata in policy")

    def is_prohibited(self, a_field: str | ProhibitedField) -> bool:
        """Return True if field must not appear in policy prose."""
        result: bool = False
        if isinstance(a_field, ProhibitedField):
            result = a_field in self.prohibited_fields
        else:
            try:
                result = ProhibitedField(a_field) in self.prohibited_fields
            except ValueError:
                result = False
        return result
