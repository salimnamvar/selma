"""Cross-layer binding value objects.

Models the relationship between policy (governance intent), schema
(structural projection), and specification (normative behavior) layers.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field

from domain.base import DomainValueObject
from domain.identifiers import GovernanceText


class ConflictResolutionBinding(DomainValueObject):
    """How each layer contributes to conflict resolution.

    Mirrors ``cross_layer_binding.conflict_resolution_binding`` in the doctrine.
    Cross-layer *precedence mapping* lives under
    ``priority_hierarchy.cross_layer_precedence`` as ``CrossLayerPrecedence``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    policy: GovernanceText = Field(description="Policy layer's role in conflict resolution")
    schema_layer: GovernanceText = Field(
        alias="schema",
        description="Schema layer's role in conflict resolution",
    )
    spec: GovernanceText = Field(description="Specification layer's role in conflict resolution")
    precedence: GovernanceText = Field(description="Declared precedence chain")


class FieldLegality(DomainValueObject):
    """Defines what each layer may contain."""

    policy_layer: GovernanceText = Field(description="What the policy layer may contain")
    schema_layer: GovernanceText = Field(description="What the schema layer may contain")
    spec_layer: GovernanceText = Field(description="What the specification layer may contain")


class CrossLayerBinding(DomainValueObject):
    """Structural relationship between policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    normative_source: GovernanceText = Field(description="The authoritative behavioral source")
    policy_layer_purpose: GovernanceText = Field(
        alias="this_layer_purpose",
        description="Purpose of the policy (this) layer",
    )
    schema_layer_purpose: GovernanceText = Field(description="Purpose of the schema layer")
    enforcement: GovernanceText = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: GovernanceText = Field(description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")
