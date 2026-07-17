"""Identity resolution — dual lineage / execution identity mapping."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: str = Field(min_length=1, description="What Machine ID represents")
    exclusions: tuple[str, ...] = Field(min_length=1, description="What Machine ID is not")
    assignment: str = Field(min_length=1, description="How Machine ID is assigned")
    governance_intent: str = Field(min_length=1, description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """How identities map across policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_field: str = Field(min_length=1, description="The canonical identity field name")
    policy_location: str = Field(min_length=1, description="Where identity appears in policy")
    schema_lineage_location: str = Field(min_length=1, description="Where lineage ID appears in schema")
    schema_execution_location: str = Field(min_length=1, description="Where execution ID appears in schema")
    spec_lineage_location: str = Field(min_length=1, description="Where lineage ID appears in spec")
    spec_execution_location: str = Field(min_length=1, description="Where execution ID appears in spec")
    identity_mapping: str = Field(min_length=1, description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: str = Field(min_length=1, description="Uniqueness constraint for lineage IDs")
    lifecycle_reference: str = Field(min_length=1, description="Reference to identity lifecycle operations")
