from pydantic import BaseModel, ConfigDict, Field


class ConflictResolutionBinding(BaseModel):
    """Describes how each layer contributes to conflict resolution,
    including the normative algorithm location and precedence chain."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    policy: str = Field(description="Policy layer's role in conflict resolution")
    schema_layer: str = Field(alias="schema", description="Schema layer's role in conflict resolution")
    spec: str = Field(description="Specification layer's role in conflict resolution")
    precedence: str = Field(description="Declared precedence chain")
    normative_algorithm: str = Field(description="Where the normative resolution algorithm is defined")
    structural_override: str = Field(description="Schema-level override mechanism for conflict resolution")


class FieldLegality(BaseModel):
    """Defines what each layer may contain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_layer: str = Field(description="What the policy layer may contain")
    schema_layer: str = Field(description="What the schema layer may contain")
    spec_layer: str = Field(description="What the specification layer may contain")


class CrossLayerBinding(BaseModel):
    """Describes the structural relationship between policy, schema,
    and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_source: str = Field(description="The authoritative behavioral source")
    policy_layer_purpose: str = Field(description="Purpose of the policy layer")
    schema_layer_purpose: str = Field(description="Purpose of the schema layer")
    enforcement: str = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: str = Field(description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")
