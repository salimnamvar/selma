"""Identity Resolution Value Objects."""

from __future__ import annotations

from pydantic import Field

from domain.base import DomainValueObject
from domain.identifiers import FieldPath, GovernanceText


class MachineIdSemantics(DomainValueObject):
    """Defines the semantics of the Machine ID concept."""

    definition: GovernanceText = Field(description="What Machine ID represents")
    exclusions: tuple[GovernanceText, ...] = Field(
        alias="not",
        description="What Machine ID is not",
    )
    assignment: GovernanceText = Field(description="How Machine ID is assigned")
    governance_intent: GovernanceText = Field(description="Why Machine ID matters for governance")


class IdentityResolution(DomainValueObject):
    """How identities map across policy, schema, and specification layers."""

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
