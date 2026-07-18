"""Cross-layer binding — policy / schema / spec relationship constraints."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ConflictResolutionBinding(BaseModel):
    """How each layer contributes to conflict resolution (declarative intent)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_layer: str = Field(min_length=1, description="Policy layer's role in conflict resolution")
    schema_layer: str = Field(min_length=1, description="Schema layer's role in conflict resolution")
    spec_layer: str = Field(min_length=1, description="Specification layer's role in conflict resolution")
    precedence: str = Field(min_length=1, description="Declared precedence chain as governance prose (not executable)")


class FieldLegality(BaseModel):
    """Defines what each layer may contain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_layer: str = Field(min_length=1, description="What the policy layer may contain")
    schema_layer: str = Field(min_length=1, description="What the schema layer may contain")
    spec_layer: str = Field(min_length=1, description="What the specification layer may contain")


class CrossLayerBinding(BaseModel):
    """Structural relationship between policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_source: str = Field(min_length=1, description="The authoritative behavioral source")
    policy_purpose: str = Field(min_length=1, description="Purpose of the policy (this) layer")
    schema_purpose: str = Field(min_length=1, description="Purpose of the schema layer")
    enforcement: str = Field(min_length=1, description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: str = Field(min_length=1, description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")
