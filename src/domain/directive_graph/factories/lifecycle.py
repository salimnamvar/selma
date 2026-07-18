"""Lifecycle factory — fork, merge, split, retire, activate, revise, rename.

Encapsulates identity rules from SPECIFICATION.md §2.2 / §2.2.2 and returns
new immutable graphs plus domain events.

Catalog FSM: docs/state-machine/selma_directive_lifecycle.puml
Design events (STM-032): DirectiveCreated, DirectiveRevised (internal on
Draft/Active — STM-018/035), DirectivePublished, DirectiveRetired,
DirectiveSuperseded, DirectiveRestored, DirectiveForked / Merged / Split,
DirectiveChildrenSpawned, Finalized. Unhandled-event policy: reject.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import TYPE_CHECKING

from domain.directive_graph.enums import DirectiveStatus
from domain.directive_graph.enums import LineageOperation
from domain.directive_graph.events import DirectiveActivated
from domain.directive_graph.events import DirectiveForked
from domain.directive_graph.events import DirectiveMerged
from domain.directive_graph.events import DirectiveRenamed
from domain.directive_graph.events import DirectiveRetired
from domain.directive_graph.events import DirectiveRevised
from domain.directive_graph.events import DirectiveSplit
from domain.directive_graph.events import DirectiveSuperseded
from domain.directive_graph.exceptions import DirectiveNotFoundError
from domain.directive_graph.exceptions import InvalidLifecycleTransitionError
from domain.directive_graph.exceptions import LifecycleInvariantError
from domain.directive_graph.value_objects.lineage import Lineage
from domain.shared.events import DomainEvent

if TYPE_CHECKING:
    from domain.directive_graph.directive import Directive
    from domain.directive_graph.directive_graph import DirectiveGraph
    from domain.directive_graph.scalars import ExecutionId
    from domain.directive_graph.scalars import UtcTimestamp


@dataclass(frozen=True)
class LifecycleResult:
    """Outcome of a lifecycle operation.

    Attributes:
        graph: The new DirectiveGraph after the operation.
        events: Domain events raised by the operation.
    """

    graph: DirectiveGraph
    events: tuple[DomainEvent, ...]


def _event_meta() -> dict[str, str]:
    return {
        "event_id": DomainEvent.new_id(),
        "occurred_at": DomainEvent.now_utc(),
    }


def compute_merge_execution_id(
    a_lineage_id: str,
    a_parent_lineage_ids: Sequence[str],
    a_parent_execution_ids: Sequence[str],
    a_timestamp: str,
) -> str:
    """Compute deterministic merge execution ID per SPEC §2.2.2.

    Args:
        a_lineage_id: Surviving (lexicographic min) lineage root.
        a_parent_lineage_ids: Both parent lineage IDs (any order).
        a_parent_execution_ids: Both parent execution IDs (any order).
        a_timestamp: Lineage operation timestamp.

    Returns:
        Execution ID of the form ``{lineage_id}-M{16 hex uppercase}``.
    """
    payload = {
        "operation": "merge",
        "parent_execution_ids": sorted(a_parent_execution_ids),
        "parent_lineage_ids": sorted(a_parent_lineage_ids),
        "timestamp": a_timestamp,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16].upper()
    return f"{a_lineage_id}-M{digest}"


class DirectiveLifecycleFactory:
    """Creates new DirectiveGraph instances for identity lifecycle operations.

    All methods are pure: they never mutate the input graph.
    """

    def activate(self, a_graph: DirectiveGraph, a_execution_id: ExecutionId) -> LifecycleResult:
        """Activate a draft directive.

        Args:
            a_graph: Current graph.
            a_execution_id: Directive to activate.

        Returns:
            Updated graph and ``DirectiveActivated`` event.
        """
        directive = self._require(a_graph, a_execution_id)
        activated = directive.activate()
        new_graph = a_graph.replace_directive(activated)
        event = DirectiveActivated(
            **_event_meta(),
            execution_id=activated.id,
            lineage_id=activated.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def retire(self, a_graph: DirectiveGraph, a_execution_id: ExecutionId) -> LifecycleResult:
        """Retire an active directive (status → deprecated).

        Args:
            a_graph: Current graph.
            a_execution_id: Directive to retire.

        Returns:
            Updated graph and ``DirectiveRetired`` event.
        """
        directive = self._require(a_graph, a_execution_id)
        retired = directive.retire()
        new_graph = a_graph.replace_directive(retired)
        event = DirectiveRetired(
            **_event_meta(),
            execution_id=retired.id,
            lineage_id=retired.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def supersede(
        self,
        a_graph: DirectiveGraph,
        a_execution_id: ExecutionId,
        a_successor_id: ExecutionId,
    ) -> LifecycleResult:
        """Supersede an active directive with a successor.

        Args:
            a_graph: Current graph.
            a_execution_id: Directive being superseded.
            a_successor_id: Replacing directive (must exist and be active/draft).

        Returns:
            Updated graph and ``DirectiveSuperseded`` event.
        """
        directive = self._require(a_graph, a_execution_id)
        successor = self._require(a_graph, a_successor_id)
        if successor.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            msg = f"Successor {a_successor_id!r} must be active or draft (got {successor.status!r})"
            raise LifecycleInvariantError(msg)
        superseded = directive.supersede(a_successor_id)
        new_graph = a_graph.replace_directive(superseded)
        event = DirectiveSuperseded(
            **_event_meta(),
            execution_id=superseded.id,
            lineage_id=superseded.lineage_id,
            successor_id=a_successor_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def revise(
        self,
        a_graph: DirectiveGraph,
        a_execution_id: ExecutionId,
        a_revision: str,
        **a_field_updates: object,
    ) -> LifecycleResult:
        """Revise a directive (same identity; no lineage record required).

        Args:
            a_graph: Current graph.
            a_execution_id: Directive to revise.
            a_revision: New revision identifier.
            **a_field_updates: Optional non-identity field updates.

        Returns:
            Updated graph and ``DirectiveRevised`` event.
        """
        directive = self._require(a_graph, a_execution_id)
        revised = directive.with_revision(a_revision, **a_field_updates)
        new_graph = a_graph.replace_directive(revised)
        event = DirectiveRevised(
            **_event_meta(),
            execution_id=revised.id,
            lineage_id=revised.lineage_id,
            directive_revision=a_revision,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def rename(
        self,
        a_graph: DirectiveGraph,
        a_execution_id: ExecutionId,
        a_message: str,
    ) -> LifecycleResult:
        """Rename a directive message (identity unchanged).

        Args:
            a_graph: Current graph.
            a_execution_id: Directive to rename.
            a_message: New human-readable message.

        Returns:
            Updated graph and ``DirectiveRenamed`` event.
        """
        directive = self._require(a_graph, a_execution_id)
        renamed = directive.with_message(a_message)
        new_graph = a_graph.replace_directive(renamed)
        event = DirectiveRenamed(
            **_event_meta(),
            execution_id=renamed.id,
            lineage_id=renamed.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def fork(
        self,
        a_graph: DirectiveGraph,
        a_parent_execution_id: ExecutionId,
        a_child_execution_ids: tuple[ExecutionId, ExecutionId],
        a_timestamp: UtcTimestamp,
        a_reason: str | None = None,
    ) -> LifecycleResult:
        """Fork a parent into two new execution IDs sharing the lineage root.

        The parent is retired (deprecated). Children inherit ``lineage_id`` and
        receive ``lineage.operation=fork``.

        Args:
            a_graph: Current graph.
            a_parent_execution_id: Source directive.
            a_child_execution_ids: Two new unique execution IDs.
            a_timestamp: Operation timestamp (UTC).
            a_reason: Optional human-readable reason.

        Returns:
            Updated graph and ``DirectiveForked`` event.
        """
        parent = self._require(a_graph, a_parent_execution_id)
        if parent.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            msg = f"Cannot fork directive {a_parent_execution_id!r} with status {parent.status!r}"
            raise InvalidLifecycleTransitionError(msg)
        if a_child_execution_ids[0] == a_child_execution_ids[1]:
            msg = "Fork child execution IDs must be distinct"
            raise LifecycleInvariantError(msg)
        for cid in a_child_execution_ids:
            if cid in a_graph.execution_ids():
                msg = f"Execution ID already exists: {cid!r}"
                raise LifecycleInvariantError(msg)
            if cid == parent.id:
                msg = "Fork child ID must not equal parent ID"
                raise LifecycleInvariantError(msg)

        lineage = Lineage(
            operation=LineageOperation.FORK,
            parent_lineage_ids=(parent.lineage_id,),
            parent_execution_ids=(parent.id,),
            timestamp=a_timestamp,
            reason=a_reason,
        )
        children = tuple(
            parent.model_copy(
                update={
                    "id": cid,
                    "lineage_id": parent.lineage_id,
                    "lineage": lineage,
                    "status": DirectiveStatus.DRAFT,
                    "created_at": a_timestamp,
                }
            )
            for cid in a_child_execution_ids
        )
        retired_parent = parent.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        new_graph = a_graph.with_directives(self._replace_and_append(a_graph.directives, retired_parent, children))
        event = DirectiveForked(
            **_event_meta(),
            parent_execution_id=parent.id,
            lineage_id=parent.lineage_id,
            child_execution_ids=a_child_execution_ids,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def merge(
        self,
        a_graph: DirectiveGraph,
        a_parent_a_id: ExecutionId,
        a_parent_b_id: ExecutionId,
        a_timestamp: UtcTimestamp,
        a_reason: str | None = None,
        a_merged_message: str | None = None,
    ) -> LifecycleResult:
        """Merge two directives into one new execution ID (SPEC §2.2.2).

        Both parents are deprecated. Surviving ``lineage_id`` is the
        lexicographic minimum of the parents' lineage IDs.

        Args:
            a_graph: Current graph.
            a_parent_a_id: First parent execution ID.
            a_parent_b_id: Second parent execution ID.
            a_timestamp: Operation timestamp (UTC).
            a_reason: Optional human-readable reason.
            a_merged_message: Optional message for the merged directive;
                defaults to parent A's message.

        Returns:
            Updated graph and ``DirectiveMerged`` event.
        """
        if a_parent_a_id == a_parent_b_id:
            msg = "Cannot merge a directive with itself"
            raise LifecycleInvariantError(msg)
        parent_a = self._require(a_graph, a_parent_a_id)
        parent_b = self._require(a_graph, a_parent_b_id)
        for p in (parent_a, parent_b):
            if p.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
                msg = f"Cannot merge directive {p.id!r} with status {p.status!r}"
                raise InvalidLifecycleTransitionError(msg)

        # SPEC §2.2.2: sorted parent sets; merge cardinality is always 2 entries.
        # When both parents share one lineage_id (post-fork siblings), both slots
        # still carry that lineage_id so parent_lineage_ids length remains 2.
        sorted_lineage = tuple(sorted([parent_a.lineage_id, parent_b.lineage_id]))
        sorted_exec = tuple(sorted([parent_a.id, parent_b.id]))
        surviving_lineage = min(parent_a.lineage_id, parent_b.lineage_id)
        merged_id = compute_merge_execution_id(
            surviving_lineage,
            sorted_lineage,
            sorted_exec,
            a_timestamp,
        )
        if merged_id in a_graph.execution_ids():
            msg = f"Merge execution ID already exists: {merged_id!r}"
            raise LifecycleInvariantError(msg)

        lineage = Lineage(
            operation=LineageOperation.MERGE,
            parent_lineage_ids=sorted_lineage,
            parent_execution_ids=sorted_exec,
            timestamp=a_timestamp,
            reason=a_reason,
        )
        # Prefer content from the parent whose lineage root survives.
        base = parent_a if parent_a.lineage_id == surviving_lineage else parent_b
        merged = base.model_copy(
            update={
                "id": merged_id,
                "lineage_id": surviving_lineage,
                "lineage": lineage,
                "status": DirectiveStatus.DRAFT,
                "created_at": a_timestamp,
                "message": a_merged_message if a_merged_message is not None else base.message,
            }
        )
        retired_a = parent_a.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        retired_b = parent_b.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        replaced = {retired_a.id: retired_a, retired_b.id: retired_b}
        new_directives = (*(replaced.get(d.id, d) for d in a_graph.directives), merged)
        new_graph = a_graph.with_directives(new_directives)
        event = DirectiveMerged(
            **_event_meta(),
            parent_execution_ids=sorted_exec,
            parent_lineage_ids=lineage.parent_lineage_ids,
            merged_execution_id=merged_id,
            merged_lineage_id=surviving_lineage,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def split(
        self,
        a_graph: DirectiveGraph,
        a_parent_execution_id: ExecutionId,
        a_child_execution_ids: tuple[ExecutionId, ...],
        a_timestamp: UtcTimestamp,
        a_reason: str | None = None,
    ) -> LifecycleResult:
        """Split a parent into multiple new execution IDs sharing the lineage root.

        Args:
            a_graph: Current graph.
            a_parent_execution_id: Source directive.
            a_child_execution_ids: Two or more new unique execution IDs.
            a_timestamp: Operation timestamp (UTC).
            a_reason: Optional human-readable reason.

        Returns:
            Updated graph and ``DirectiveSplit`` event.
        """
        parent = self._require(a_graph, a_parent_execution_id)
        if parent.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            msg = f"Cannot split directive {a_parent_execution_id!r} with status {parent.status!r}"
            raise InvalidLifecycleTransitionError(msg)
        if len(a_child_execution_ids) < 2:
            msg = "Split requires at least 2 child execution IDs"
            raise LifecycleInvariantError(msg)
        if len(a_child_execution_ids) != len(set(a_child_execution_ids)):
            msg = "Split child execution IDs must be unique"
            raise LifecycleInvariantError(msg)
        for cid in a_child_execution_ids:
            if cid in a_graph.execution_ids():
                msg = f"Execution ID already exists: {cid!r}"
                raise LifecycleInvariantError(msg)
            if cid == parent.id:
                msg = "Split child ID must not equal parent ID"
                raise LifecycleInvariantError(msg)

        lineage = Lineage(
            operation=LineageOperation.SPLIT,
            parent_lineage_ids=(parent.lineage_id,),
            parent_execution_ids=(parent.id,),
            timestamp=a_timestamp,
            reason=a_reason,
        )
        children = tuple(
            parent.model_copy(
                update={
                    "id": cid,
                    "lineage_id": parent.lineage_id,
                    "lineage": lineage,
                    "status": DirectiveStatus.DRAFT,
                    "created_at": a_timestamp,
                }
            )
            for cid in a_child_execution_ids
        )
        retired_parent = parent.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        new_graph = a_graph.with_directives(self._replace_and_append(a_graph.directives, retired_parent, children))
        event = DirectiveSplit(
            **_event_meta(),
            parent_execution_id=parent.id,
            lineage_id=parent.lineage_id,
            child_execution_ids=a_child_execution_ids,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require(a_graph: DirectiveGraph, a_execution_id: ExecutionId) -> Directive:
        directive = a_graph.get_by_id(a_execution_id)
        if directive is None:
            raise DirectiveNotFoundError(a_execution_id)
        return directive

    @staticmethod
    def _replace_and_append(
        a_directives: tuple[Directive, ...],
        a_replacement: Directive,
        a_extras: tuple[Directive, ...],
    ) -> tuple[Directive, ...]:
        updated = tuple(a_replacement if d.id == a_replacement.id else d for d in a_directives)
        return updated + a_extras
