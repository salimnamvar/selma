"""Contamination Guard Value Objects.

Policy-layer field constraints that keep executable schema fields out of prose.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple, Union

from pydantic import Field

from domain.base import DomainValueObject
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ContaminationGuard(DomainValueObject):
    """Defines what is prohibited and allowed in the policy layer.

    Attributes:
        prohibited_fields (FrozenSet[ProhibitedField]): Prohibited schema fields.
        allowed_machine_references (Tuple[GovernanceText, ...]): Allowed Machine ID uses.
        metadata_note (GovernanceText): Constraints on schema metadata in policy.
    """

    prohibited_fields: FrozenSet[ProhibitedField] = Field(
        min_length=1,
        description="Schema fields that must not appear in policy prose",
    )
    allowed_machine_references: Tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_note: GovernanceText = Field(description="Constraints on schema metadata in policy")

    def is_prohibited(self, a_field: Union[str, ProhibitedField]) -> bool:
        """Return True if field must not appear in policy prose.

        Args:
            a_field (Union[str, ProhibitedField]): Field name or enum member.

        Returns:
            bool: True if the field is prohibited.
        """
        result: bool = False
        if isinstance(a_field, ProhibitedField):
            result = a_field in self.prohibited_fields
        else:
            try:
                result = ProhibitedField(a_field) in self.prohibited_fields
            except ValueError:
                result = False
        return result
