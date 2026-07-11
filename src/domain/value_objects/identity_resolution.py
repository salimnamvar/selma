"""Identity resolution — dual lineage / execution identity mapping."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from domain.base import VO_CONFIG
from domain.identifiers import FieldPath, GovernanceText, field_path_field, field_path_is_field


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = VO_CONFIG

    definition: GovernanceText = Field(description="What Machine ID represents")
    exclusions: tuple[GovernanceText, ...] = Field(description="What Machine ID is not")
    assignment: GovernanceText = Field(description="How Machine ID is assigned")
    governance_intent: GovernanceText = Field(description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """How identities map across policy, schema, and specification layers."""

    model_config = VO_CONFIG

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
        if not field_path_is_field(self.schema_lineage_location, "lineage_id"):
            raise ValueError(
                "schema_lineage_location must reference field 'lineage_id' "
                f"(got {field_path_field(self.schema_lineage_location)!r})"
            )
        if not field_path_is_field(self.schema_execution_location, "id"):
            raise ValueError(
                "schema_execution_location must reference field 'id' "
                f"(got {field_path_field(self.schema_execution_location)!r})"
            )
        if not field_path_is_field(self.spec_lineage_location, "lineage_id"):
            raise ValueError(
                "spec_lineage_location must reference field 'lineage_id' "
                f"(got {field_path_field(self.spec_lineage_location)!r})"
            )
        if not field_path_is_field(self.spec_execution_location, "directive_id"):
            raise ValueError(
                "spec_execution_location must reference field 'directive_id' "
                f"(got {field_path_field(self.spec_execution_location)!r})"
            )
        return self