from typing import List

from pydantic import BaseModel, Field


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = {"frozen": True}

    definition: str = Field(description="What Machine ID represents")
    not_descriptions: List[str] = Field(alias="not", description="What Machine ID is not")
    assignment: str = Field(description="How Machine ID is assigned")
    governance_intent: str = Field(description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """Describes how identities map across policy, schema, and specification layers."""

    model_config = {"frozen": True}

    canonical_field: str = Field(description="The canonical identity field name")
    policy_location: str = Field(description="Where identity appears in policy")
    schema_lineage_location: str = Field(description="Where lineage ID appears in schema")
    schema_execution_location: str = Field(description="Where execution ID appears in schema")
    spec_lineage_location: str = Field(description="Where lineage ID appears in spec")
    spec_execution_location: str = Field(description="Where execution ID appears in spec")
    rule: str = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: str = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle: str = Field(description="Reference to identity lifecycle operations")
