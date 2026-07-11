"""Contamination Guard Value Objects.

Policy-layer field constraints that keep executable schema fields out of prose.
"""

from __future__ import annotations

from typing import FrozenSet, Tuple, Union

from pydantic import Field, field_validator, model_validator

from domain.base import DomainValueObject
from domain.enums import ProhibitedField
from domain.identifiers import GovernanceText


class ProhibitedFieldSet(DomainValueObject):
    """Set of schema fields prohibited in policy prose.

    Attributes:
        fields (FrozenSet[ProhibitedField]): Prohibited schema fields.
    """

    fields: FrozenSet[ProhibitedField] = Field(description="Schema fields that must not appear in policy prose")

    @model_validator(mode="after")
    def check_non_empty(self) -> ProhibitedFieldSet:
        """Reject an empty prohibited-field set.

        Returns:
            ProhibitedFieldSet: Validated instance.

        Raises:
            ValueError: If the field set is empty.
        """
        result: ProhibitedFieldSet = self
        if not self.fields:
            raise ValueError("Prohibited field set must not be empty")
        return result

    def contains(self, a_field: Union[str, ProhibitedField]) -> bool:
        """Return True if field is prohibited in policy prose.

        Args:
            a_field (Union[str, ProhibitedField]): Field name or enum member.

        Returns:
            bool: True if the field is prohibited.
        """
        result: bool = False
        if isinstance(a_field, ProhibitedField):
            result = a_field in self.fields
        else:
            try:
                result = ProhibitedField(a_field) in self.fields
            except ValueError:
                result = False
        return result

    def __contains__(self, a_item: object) -> bool:
        result: bool = False
        if isinstance(a_item, (str, ProhibitedField)):
            result = self.contains(a_item)
        return result

    def __len__(self) -> int:
        return len(self.fields)


class ContaminationGuard(DomainValueObject):
    """Defines what is prohibited and allowed in the policy layer.

    Attributes:
        prohibited_fields (FrozenSet[ProhibitedField]): Prohibited schema fields.
        allowed_machine_references (Tuple[GovernanceText, ...]): Allowed Machine ID uses.
        metadata_note (GovernanceText): Constraints on schema metadata in policy.
    """

    prohibited_fields: FrozenSet[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: Tuple[GovernanceText, ...] = Field(
        min_length=1,
        description="How Machine IDs may appear in policy",
    )
    metadata_note: GovernanceText = Field(description="Constraints on schema metadata in policy")

    @field_validator("prohibited_fields")
    @classmethod
    def check_prohibited_non_empty(
        cls,
        a_value: FrozenSet[ProhibitedField],
    ) -> FrozenSet[ProhibitedField]:
        """Reject an empty prohibited_fields collection.

        Args:
            a_value (FrozenSet[ProhibitedField]): Candidate field set.

        Returns:
            FrozenSet[ProhibitedField]: Validated field set.

        Raises:
            ValueError: If the collection is empty.
        """
        result: FrozenSet[ProhibitedField] = a_value
        if not a_value:
            raise ValueError("prohibited_fields must not be empty")
        return result

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

    def as_field_set(self) -> ProhibitedFieldSet:
        """Return prohibited fields wrapped as a queryable set.

        Returns:
            ProhibitedFieldSet: Queryable prohibited field set.
        """
        result: ProhibitedFieldSet = ProhibitedFieldSet(fields=self.prohibited_fields)
        return result
