"""DirectiveGraph aggregate root.

The ``DirectiveGraph`` is the sole aggregate root for the Directive Graph
bounded context.  It owns all ``Directive`` entities and enforces the
transactional consistency boundary.

Cross-directive invariants (uniqueness, reference integrity, cycle detection,
complexity budgets) are enforced by domain services via specifications — NOT
inside this model.  The model enforces only structural validity (Pydantic
``Field`` constraints).

Lifecycle mutations are provided by ``DirectiveLifecycleFactory`` and return
new frozen ``DirectiveGraph`` instances plus domain events.

Domain shape only: the JSON ``rules`` array is mapped to ``directives`` by
the anti-corruption layer.

Reference: SPECIFICATION.md §2.1-2.2
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.directive_graph.directive import Directive
from domain.directive_graph.scalars import ExecutionId, LineageId, PolicyContractId, SemanticVersion
from domain.directive_graph.value_objects.metadata import DatasetMetadata


class DirectiveGraph(BaseModel):
    """Versioned, self-consistent collection of directives.

    This is the transactional consistency boundary for the entire directive
    dataset.  Lifecycle operations (fork, merge, split, retire, …) produce
    new ``DirectiveGraph`` instances via ``DirectiveLifecycleFactory``.

    Attributes:
        version: Semantic version of this dataset.
        policy_contract_version: Paired policy doctrine version.
        policy_contract_id: Always ``"universal-policy-doctrine"``.
        metadata: Dataset-level informational metadata.
        directives: Ordered collection of directives.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: SemanticVersion
    policy_contract_version: SemanticVersion
    policy_contract_id: PolicyContractId
    metadata: DatasetMetadata | None = None
    directives: tuple[Directive, ...] = Field(
        min_length=1,
        description="Ordered collection of directives.",
    )

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    def get_by_id(self, execution_id: ExecutionId) -> Directive | None:
        """Return the directive with the given execution ID, or ``None``.

        Args:
            execution_id: The execution ID to look up.

        Returns:
            Matching directive, or None if not found.
        """
        for directive in self.directives:
            if directive.id == execution_id:
                return directive
        return None

    def get_by_lineage_id(self, lineage_id: LineageId) -> list[Directive]:
        """Return all directives sharing the given lineage ID.

        After fork or split operations there may be multiple directives with
        the same ``lineage_id`` (SPECIFICATION.md §2.3).

        Args:
            lineage_id: The lineage ID to look up.

        Returns:
            All matching directives (may be empty).
        """
        return [d for d in self.directives if d.lineage_id == lineage_id]

    def execution_ids(self) -> frozenset[ExecutionId]:
        """Return a frozenset of all execution IDs in this graph.

        Returns:
            Set of all execution IDs.
        """
        return frozenset(d.id for d in self.directives)

    def lineage_ids(self) -> frozenset[LineageId]:
        """Return a frozenset of all lineage IDs in this graph.

        After fork/split operations the count may be smaller than
        ``len(self.directives)``.

        Returns:
            Set of all lineage IDs.
        """
        return frozenset(d.lineage_id for d in self.directives)

    # ------------------------------------------------------------------
    # Structural copy helpers used by lifecycle factory
    # ------------------------------------------------------------------

    def replace_directive(self, directive: Directive) -> DirectiveGraph:
        """Return a new graph with the directive of matching ``id`` replaced.

        Args:
            directive: Replacement directive (must already exist by id).

        Returns:
            New frozen graph.

        Raises:
            ValueError: If no directive with the same id exists.
        """
        found = False
        new_directives: list[Directive] = []
        for d in self.directives:
            if d.id == directive.id:
                new_directives.append(directive)
                found = True
            else:
                new_directives.append(d)
        if not found:
            raise ValueError(f"Cannot replace unknown directive id {directive.id!r}")
        return self.model_copy(update={"directives": tuple(new_directives)})

    def with_directives(self, directives: tuple[Directive, ...]) -> DirectiveGraph:
        """Return a new graph with the given directives collection.

        Args:
            directives: Full replacement collection (must be non-empty).

        Returns:
            New frozen graph.
        """
        return self.model_copy(update={"directives": directives})
