"""Identity Resolution Value Objects.

Cross-layer identity mapping and Machine ID semantics.
"""

from __future__ import annotations

from typing import Tuple

from pydantic import ConfigDict, Field

from domain.base import DomainValueObject
from domain.identifiers import FieldPath, GovernanceText


class MachineIdSemantics(DomainValueObject):
    """Defines the semantics of the Machine ID concept.

    Attributes:
        definition (GovernanceText): What Machine ID represents.
        exclusions (Tuple[GovernanceText, ...]): What Machine ID is not.
        assignment (GovernanceText): How Machine ID is assigned.
        governance_intent (GovernanceText): Why Machine ID matters for governance.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    definition: GovernanceText = Field(description="What Machine ID represents")
    exclusions: Tuple[GovernanceText, ...] = Field(
        alias="not",
        description="What Machine ID is not",
    )
    assignment: GovernanceText = Field(description="How Machine ID is assigned")
    governance_intent: GovernanceText = Field(description="Why Machine ID matters for governance")


class IdentityResolution(DomainValueObject):
    """How identities map across policy, schema, and specification layers.

    Attributes:
        canonical_field (GovernanceText): Canonical identity field name.
        policy_location (FieldPath): Where identity appears in policy.
        schema_lineage_location (FieldPath): Where lineage ID appears in schema.
        schema_execution_location (FieldPath): Where execution ID appears in schema.
        spec_lineage_location (FieldPath): Where lineage ID appears in spec.
        spec_execution_location (FieldPath): Where execution ID appears in spec.
        rule (GovernanceText): Identity mapping rule.
        machine_id_semantics (MachineIdSemantics): Detailed Machine ID semantics.
        uniqueness (GovernanceText): Uniqueness constraint for lineage IDs.
        lifecycle (GovernanceText): Reference to identity lifecycle operations.
    """

    canonical_field: GovernanceText = Field(description="The canonical identity field name")
    policy_location: FieldPath = Field(description="Where identity appears in policy")
    schema_lineage_location: FieldPath = Field(description="Where lineage ID appears in schema")
    schema_execution_location: FieldPath = Field(description="Where execution ID appears in schema")
    spec_lineage_location: FieldPath = Field(description="Where lineage ID appears in spec")
    spec_execution_location: FieldPath = Field(description="Where execution ID appears in spec")
    rule: GovernanceText = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: GovernanceText = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle: GovernanceText = Field(description="Reference to identity lifecycle operations")
