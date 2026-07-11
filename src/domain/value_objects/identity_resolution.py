"""Identity resolution — dual lineage / execution identity mapping."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.identifiers import GovernanceText


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
    policy_location: GovernanceText = Field(description="Where identity appears in policy")
    schema_lineage_location: GovernanceText = Field(description="Where lineage ID appears in schema")
    schema_execution_location: GovernanceText = Field(description="Where execution ID appears in schema")
    spec_lineage_location: GovernanceText = Field(description="Where lineage ID appears in spec")
    spec_execution_location: GovernanceText = Field(description="Where execution ID appears in spec")
    identity_mapping: GovernanceText = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: GovernanceText = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle_reference: GovernanceText = Field(description="Reference to identity lifecycle operations")