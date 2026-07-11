from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Prose


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    definition: Prose = Field(description="What Machine ID represents")
    exclusions: tuple[Prose, ...] = Field(alias="not", description="What Machine ID is not")
    assignment: Prose = Field(description="How Machine ID is assigned")
    governance_intent: Prose = Field(description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """Describes how identities map across policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_field: str = Field(description="The canonical identity field name")
    policy_location: str = Field(description="Where identity appears in policy")
    schema_lineage_location: str = Field(description="Where lineage ID appears in schema")
    schema_execution_location: str = Field(description="Where execution ID appears in schema")
    spec_lineage_location: str = Field(description="Where lineage ID appears in spec")
    spec_execution_location: str = Field(description="Where execution ID appears in spec")
    rule: Prose = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: Prose = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle: Prose = Field(description="Reference to identity lifecycle operations")
