from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Prose


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    definition: Prose = Field(description="What Machine ID represents")
    exclusions: tuple[Prose, ...] = Field(description="What Machine ID is not")
    assignment_rule: Prose = Field(description="How Machine ID is assigned")
    intent: Prose = Field(description="Why Machine ID matters for governance")


class IdentityPolicy(BaseModel):
    """Cohesive governance policy for identity across layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_field: str = Field(description="The canonical identity field name")
    mapping_rule: Prose = Field(description="Identity mapping rule across layers")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness_pattern: str = Field(description="Regex pattern for lineage ID uniqueness")
