"""Cross-layer binding — policy / schema / spec relationship constraints.

Declares governance *intent* only. Conflict resolution *algorithms* belong
to SPECIFICATION.md / the compilation engine — not this layer.
"""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.identifiers import (
    GovernanceConstraint,
    GovernanceDescription,
    GovernancePurpose,
)


class ConflictResolutionIntent(DomainValueObject):
    """How each layer contributes to conflict resolution (declarative intent)."""

    policy_layer: GovernancePurpose = Field(
        description="Policy layer's role in conflict resolution"
    )
    schema_layer: GovernancePurpose = Field(
        description="Schema layer's role in conflict resolution"
    )
    spec_layer: GovernancePurpose = Field(
        description="Specification layer's role in conflict resolution"
    )
    precedence: GovernanceDescription = Field(
        description="Declared precedence chain as governance prose (not executable)"
    )


# Backward-compatible name used in earlier iterations.
ConflictResolutionBinding = ConflictResolutionIntent


class FieldLegality(DomainValueObject):
    """Defines what each layer may contain."""

    policy_layer: GovernanceConstraint = Field(description="What the policy layer may contain")
    schema_layer: GovernanceConstraint = Field(description="What the schema layer may contain")
    spec_layer: GovernanceConstraint = Field(description="What the specification layer may contain")


class CrossLayerBinding(DomainValueObject):
    """Structural relationship between policy, schema, and specification layers."""

    normative_source: GovernanceDescription = Field(
        description="The authoritative behavioral source"
    )
    policy_purpose: GovernancePurpose = Field(description="Purpose of the policy (this) layer")
    schema_purpose: GovernancePurpose = Field(description="Purpose of the schema layer")
    enforcement: GovernanceDescription = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionIntent = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: GovernanceConstraint = Field(
        description="What this file must not do at runtime"
    )
    field_legality: FieldLegality = Field(description="What each layer may contain")
