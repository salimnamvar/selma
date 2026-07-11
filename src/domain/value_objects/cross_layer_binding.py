"""Cross-Layer Binding Value Objects.

Models the relationship between policy, schema, and specification layers.
"""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.identifiers import GovernanceText


class ConflictResolutionBinding(DomainValueObject):
    """How each layer contributes to conflict resolution.

    Attributes:
        policy (GovernanceText): Policy layer role in conflict resolution.
        schema_layer (GovernanceText): Schema layer role in conflict resolution.
        spec (GovernanceText): Specification layer role in conflict resolution.
        precedence (GovernanceText): Declared precedence chain.
    """

    policy: GovernanceText = Field(description="Policy layer's role in conflict resolution")
    schema_layer: GovernanceText = Field(
        alias="schema",
        description="Schema layer's role in conflict resolution",
    )
    spec: GovernanceText = Field(description="Specification layer's role in conflict resolution")
    precedence: GovernanceText = Field(description="Declared precedence chain")


class FieldLegality(DomainValueObject):
    """Defines what each layer may contain.

    Attributes:
        policy_layer (GovernanceText): What the policy layer may contain.
        schema_layer (GovernanceText): What the schema layer may contain.
        spec_layer (GovernanceText): What the specification layer may contain.
    """

    policy_layer: GovernanceText = Field(description="What the policy layer may contain")
    schema_layer: GovernanceText = Field(description="What the schema layer may contain")
    spec_layer: GovernanceText = Field(description="What the specification layer may contain")


class CrossLayerBinding(DomainValueObject):
    """Structural relationship between policy, schema, and specification layers.

    Attributes:
        normative_source (GovernanceText): The authoritative behavioral source.
        policy_layer_purpose (GovernanceText): Purpose of the policy layer.
        schema_layer_purpose (GovernanceText): Purpose of the schema layer.
        enforcement (GovernanceText): How governance intent is enforced.
        conflict_resolution_binding (ConflictResolutionBinding): Layer conflict roles.
        runtime_prohibition (GovernanceText): Runtime prohibition for this file.
        field_legality (FieldLegality): Per-layer field legality.
    """

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
