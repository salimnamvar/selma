"""DirectiveGraph aggregate root.

The ``DirectiveGraph`` is the sole aggregate root for the Directive Graph
bounded context.  It owns all ``Directive`` entities and enforces the
transactional consistency boundary.

Cross-directive invariants (uniqueness, reference integrity, cycle detection,
complexity budgets) are enforced by domain services via specifications — NOT
inside this model.  The model enforces only structural validity (Pydantic
``Field`` constraints).

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.1, §3
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.directive_graph.directive import Directive
from domain.directive_graph.scalars import (
    ExecutionId,
    LineageId,
    PolicyContractId,
    SemanticVersion,
)
from domain.directive_graph.value_objects.metadata import DatasetMetadata


class DirectiveGraph(BaseModel):
    """Versioned, self-consistent collection of directives.

    This is the transactional consistency boundary for the entire directive
    dataset.  All lineage operations (fork, merge, split) and lifecycle
    mutations return new ``DirectiveGraph`` instances.

    The JSON root of ``rule_schema.json`` maps to this class; the ``rules``
    array maps to ``directives``.

    Attributes:
        version (SemanticVersion): Semantic version of this dataset.
        policy_contract_version (SemanticVersion): Paired policy doctrine version.
        policy_contract_id (PolicyContractId): Always ``"universal-policy-doctrine"``.
        metadata (DatasetMetadata | None): Dataset-level informational metadata.
        directives (tuple[Directive, ...]): Ordered collection of directives.
    """

    model_config = ConfigDict(extra="forbid")

    version: SemanticVersion
    policy_contract_version: SemanticVersion
    policy_contract_id: PolicyContractId
    metadata: DatasetMetadata | None = None
    directives: tuple[Directive, ...] = Field(
        min_length=1,
        alias="rules",
        description="Ordered collection of directives (JSON: rules[]).",
    )

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    def get_by_id(self, execution_id: ExecutionId) -> Directive | None:
        """Return the directive with the given execution ID, or ``None``.

        Args:
            execution_id (ExecutionId): The execution ID to look up.

        Returns:
            Directive | None: Matching directive, or None if not found.
        """
        for directive in self.directives:
            if directive.id == execution_id:
                return directive
        return None

    def get_by_lineage_id(self, lineage_id: LineageId) -> list[Directive]:
        """Return all directives sharing the given lineage ID.

        After fork or split operations there may be multiple directives with
        the same ``lineage_id``.

        Args:
            lineage_id (LineageId): The lineage ID to look up.

        Returns:
            list[Directive]: All matching directives (may be empty).
        """
        return [d for d in self.directives if d.lineage_id == lineage_id]

    def execution_ids(self) -> frozenset[ExecutionId]:
        """Return a frozenset of all execution IDs in this graph.

        Returns:
            frozenset[ExecutionId]: Set of all execution IDs.
        """
        return frozenset(d.id for d in self.directives)

    def lineage_ids(self) -> frozenset[LineageId]:
        """Return a frozenset of all lineage IDs in this graph.

        After fork/split operations the count may be smaller than
        ``len(self.directives)``.

        Returns:
            frozenset[LineageId]: Set of all lineage IDs.
        """
        return frozenset(d.lineage_id for d in self.directives)
