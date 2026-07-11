"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ContaminationGuard(DomainValueObject):
    """Defines what is prohibited and allowed in the policy layer.

    Aligns with contamination_guard in policy_doctrine.yaml.
    """

    prohibited_fields: frozenset[ProhibitedField] = Field(
        min_length=1,
        description="Schema fields that must not appear in policy prose",
    )
    allowed_machine_references: tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_constraints: GovernanceText = Field(
        description="Constraints on schema metadata in policy"
    )

    @model_validator(mode="after")
    def _validate_fields(self) -> Self:
        """Ensure the guard covers the full closed vocabulary of prohibited fields."""
        missing = set(ProhibitedField) - self.prohibited_fields
        if missing:
            raise ValueError(
                f"Contamination guard missing prohibited fields: {sorted(f.value for f in missing)}"
            )
        return self

    def is_prohibited(self, key: str | ProhibitedField) -> bool:
        """Return True if field must not appear in policy prose."""
        result = False
        if isinstance(key, ProhibitedField):
            result = key in self.prohibited_fields
        else:
            try:
                result = ProhibitedField(key) in self.prohibited_fields
            except ValueError:
                result = False
        return result

    def is_allowed(self, key: str | ProhibitedField) -> bool:
        """Return True if field may appear in policy prose."""
        return not self.is_prohibited(key)

    def collect_violations(self, fields: Iterable[str | ProhibitedField]) -> tuple[str, ...]:
        """Return prohibited field names present in ``fields`` (declaration order)."""
        violations: list[str] = []
        for field in fields:
            if self.is_prohibited(field):
                violations.append(field.value if isinstance(field, ProhibitedField) else str(field))
        return tuple(violations)

    def validate_fields(self, fields: Iterable[str | ProhibitedField]) -> None:
        """Raise ValueError when any field is prohibited in policy prose."""
        violations = self.collect_violations(fields)
        if violations:
            raise ValueError(f"Prohibited policy fields: {list(violations)}")
