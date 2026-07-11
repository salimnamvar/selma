"""Contamination guard value objects."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from domain.base import DomainValueObject
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ProhibitedFieldSet(DomainValueObject):
    """Set of schema fields prohibited in policy prose, with domain queries."""

    fields: frozenset[ProhibitedField] = Field(description="Schema fields that must not appear in policy prose")

    @model_validator(mode="after")
    def check_non_empty(self) -> ProhibitedFieldSet:
        """Reject an empty prohibited-field set."""
        if not self.fields:
            raise ValueError("Prohibited field set must not be empty")
        return self

    def contains(self, field: str | ProhibitedField) -> bool:
        """Return True if *field* is prohibited in policy prose."""
        if isinstance(field, ProhibitedField):
            return field in self.fields
        try:
            return ProhibitedField(field) in self.fields
        except ValueError:
            return False

    def __contains__(self, item: object) -> bool:
        if isinstance(item, (str, ProhibitedField)):
            return self.contains(item)
        return False

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)


class ContaminationGuard(DomainValueObject):
    """Defines what is prohibited and allowed in the policy layer."""

    prohibited_fields: frozenset[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_note: GovernanceText = Field(description="Constraints on schema metadata in policy")

    @field_validator("prohibited_fields")
    @classmethod
    def check_prohibited_non_empty(
        cls,
        value: frozenset[ProhibitedField],
    ) -> frozenset[ProhibitedField]:
        """Reject an empty prohibited_fields collection."""
        if not value:
            raise ValueError("prohibited_fields must not be empty")
        return value

    def is_prohibited(self, field: str | ProhibitedField) -> bool:
        """Return True if *field* must not appear in policy prose."""
        if isinstance(field, ProhibitedField):
            return field in self.prohibited_fields
        try:
            return ProhibitedField(field) in self.prohibited_fields
        except ValueError:
            return False

    def as_field_set(self) -> ProhibitedFieldSet:
        """Return prohibited fields wrapped as a queryable set."""
        return ProhibitedFieldSet(fields=self.prohibited_fields)
