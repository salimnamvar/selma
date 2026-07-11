from pydantic import Field

from domain.enums import IdentityOperation
from domain.identifiers import Guidance
from domain.value_objects.base import DomainValueObject


class IdentityPolicy(DomainValueObject):
    """Cohesive governance policy for identity (Machine ID / Lineage ID) across layers.

    Consolidates identity resolution, lifecycle intent, and Machine ID semantics
    into a single value object that models the governance domain rather than
    the YAML document structure.
    """

    canonical_field: str = Field(description="The canonical identity field name")
    policy_location: str = Field(description="Where identity appears in policy")
    schema_lineage_location: str = Field(description="Where lineage ID appears in schema")
    schema_execution_location: str = Field(description="Where execution ID appears in schema")
    rule: Guidance = Field(description="Identity mapping rule")
    uniqueness: Guidance = Field(description="Uniqueness constraint for lineage IDs")

    machine_id_definition: Guidance = Field(description="What Machine ID represents")
    machine_id_exclusions: tuple[Guidance, ...] = Field(description="What Machine ID is not")
    machine_id_assignment: Guidance = Field(description="How Machine ID is assigned")
    machine_id_governance_intent: Guidance = Field(description="Why Machine ID matters for governance")

    revision: Guidance = Field(description="When to use revision")
    fork: Guidance = Field(description="When to use fork")
    merge: Guidance = Field(description="When to use merge")
    split: Guidance = Field(description="When to use split")
    rename: Guidance = Field(description="When to use rename")
    retire: Guidance = Field(description="When to use retire")
    dag_intent: Guidance = Field(description="Constraint on lineage ancestry graph structure")

    supported_operations: frozenset[IdentityOperation] = Field(
        default_factory=lambda: frozenset(IdentityOperation),
        description="Set of supported identity lifecycle operations",
    )

    def describe_operation(self, op: IdentityOperation) -> Guidance:
        """Return the governance guidance for a specific lifecycle operation."""
        operation_map = {
            IdentityOperation.REVISION: self.revision,
            IdentityOperation.FORK: self.fork,
            IdentityOperation.MERGE: self.merge,
            IdentityOperation.SPLIT: self.split,
            IdentityOperation.RENAME: self.rename,
            IdentityOperation.RETIRE: self.retire,
        }
        return operation_map[op]
