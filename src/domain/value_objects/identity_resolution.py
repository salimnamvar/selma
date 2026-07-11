"""Identity resolution — dual lineage / execution identity mapping."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.identifiers import FieldPath, GovernanceText


class MachineIdSemantics(DomainValueObject):
    """Defines the semantics of the Machine ID concept."""

    definition: GovernanceText = Field(description="What Machine ID represents")
    exclusions: tuple[GovernanceText, ...] = Field(description="What Machine ID is not")
    assignment: GovernanceText = Field(description="How Machine ID is assigned")
    governance_intent: GovernanceText = Field(description="Why Machine ID matters for governance")


class IdentityResolution(DomainValueObject):
    """How identities map across policy, schema, and specification layers."""

    canonical_field: GovernanceText = Field(description="The canonical identity field name")
    policy_location: FieldPath = Field(description="Where identity appears in policy")
    schema_lineage_location: FieldPath = Field(description="Where lineage ID appears in schema")
    schema_execution_location: FieldPath = Field(description="Where execution ID appears in schema")
    spec_lineage_location: FieldPath = Field(description="Where lineage ID appears in spec")
    spec_execution_location: FieldPath = Field(description="Where execution ID appears in spec")
    identity_mapping: GovernanceText = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: GovernanceText = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle_reference: GovernanceText = Field(description="Reference to identity lifecycle operations")

    @model_validator(mode="after")
    def _validate_mapping(self) -> Self:
        """Protect dual-identity meaning declared in policy doctrine."""
        if not self.schema_lineage_location.is_field("lineage_id"):
            raise ValueError(
                "schema_lineage_location must reference field 'lineage_id' "
                f"(got {self.schema_lineage_location.field!r})"
            )
        if not self.schema_execution_location.is_field("id"):
            raise ValueError(
                "schema_execution_location must reference field 'id' "
                f"(got {self.schema_execution_location.field!r})"
            )
        if not self.spec_lineage_location.is_field("lineage_id"):
            raise ValueError(
                "spec_lineage_location must reference field 'lineage_id' "
                f"(got {self.spec_lineage_location.field!r})"
            )
        if not self.spec_execution_location.is_field("directive_id"):
            raise ValueError(
                "spec_execution_location must reference field 'directive_id' "
                f"(got {self.spec_execution_location.field!r})"
            )
        return self
