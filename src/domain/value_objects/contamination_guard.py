"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from collections.abc import Iterable

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer.

    Aligns with contamination_guard in policy_doctrine.yaml.
    ``prohibited_fields`` mirrors the YAML list; enforcement uses ``ProhibitedField``.
    """

    model_config = VO_CONFIG

    prohibited_fields: frozenset[ProhibitedField] = Field(
        min_length=1,
        description="Schema fields that must not appear in policy prose (YAML mirror)",
    )
    allowed_machine_references: tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_constraints: GovernanceText = Field(
        description="Constraints on schema metadata in policy"
    )

    def is_prohibited(self, key: str | ProhibitedField) -> bool:
        """Return True if field must not appear in policy prose."""
        try:
            field = key if isinstance(key, ProhibitedField) else ProhibitedField(key)
        except ValueError:
            return False
        return field in ProhibitedField

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