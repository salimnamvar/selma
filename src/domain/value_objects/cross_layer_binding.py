"""Cross-layer binding — policy / schema / spec relationship constraints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.identifiers import GovernanceText


class ConflictResolutionIntent(BaseModel):
    """How each layer contributes to conflict resolution (declarative intent)."""

    model_config = VO_CONFIG

    policy_layer: GovernanceText = Field(description="Policy layer's role in conflict resolution")
    schema_layer: GovernanceText = Field(description="Schema layer's role in conflict resolution")
    spec_layer: GovernanceText = Field(description="Specification layer's role in conflict resolution")
    precedence: GovernanceText = Field(
        description="Declared precedence chain as governance prose (not executable)"
    )


class FieldLegality(BaseModel):
    """Defines what each layer may contain."""

    model_config = VO_CONFIG

    policy_layer: GovernanceText = Field(description="What the policy layer may contain")
    schema_layer: GovernanceText = Field(description="What the schema layer may contain")
    spec_layer: GovernanceText = Field(description="What the specification layer may contain")


class CrossLayerBinding(BaseModel):
    """Structural relationship between policy, schema, and specification layers."""

    model_config = VO_CONFIG

    normative_source: GovernanceText = Field(description="The authoritative behavioral source")
    policy_purpose: GovernanceText = Field(description="Purpose of the policy (this) layer")
    schema_purpose: GovernanceText = Field(description="Purpose of the schema layer")
    enforcement: GovernanceText = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionIntent = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: GovernanceText = Field(description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")