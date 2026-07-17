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

import hashlib
import json
from dataclasses import dataclass

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import DirectiveStatus, LineageOperation
from domain.directive_graph.events import (
    DirectiveActivated,
    DirectiveForked,
    DirectiveMerged,
    DirectiveRenamed,
    DirectiveRetired,
    DirectiveRevised,
    DirectiveSplit,
    DirectiveSuperseded,
)
from domain.directive_graph.exceptions import (
    DirectiveNotFoundError,
    InvalidLifecycleTransitionError,
    LifecycleInvariantError,
)
from domain.directive_graph.scalars import ExecutionId, UtcTimestamp
from domain.directive_graph.value_objects.lineage import Lineage
from domain.shared.events import DomainEvent


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
        "event_id": DomainEvent._new_id(),
        "occurred_at": DomainEvent._now_utc(),
    }


def compute_merge_execution_id(
    lineage_id: str,
    parent_lineage_ids: tuple[str, str],
    parent_execution_ids: tuple[str, str],
    timestamp: str,
) -> str:
    """Compute deterministic merge execution ID per SPEC §2.2.2.

    Args:
        lineage_id: Surviving (lexicographic min) lineage root.
        parent_lineage_ids: Both parent lineage IDs (any order).
        parent_execution_ids: Both parent execution IDs (any order).
        timestamp: Lineage operation timestamp.

    Returns:
        Execution ID of the form ``{lineage_id}-M{16 hex uppercase}``.
    """
    payload = {
        "operation": "merge",
        "parent_execution_ids": sorted(parent_execution_ids),
        "parent_lineage_ids": sorted(parent_lineage_ids),
        "timestamp": timestamp,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16].upper()
    return f"{lineage_id}-M{digest}"


class DirectiveLifecycleFactory:
    """Creates new DirectiveGraph instances for identity lifecycle operations.

    All methods are pure: they never mutate the input graph.
    """

    def activate(self, graph: DirectiveGraph, execution_id: ExecutionId) -> LifecycleResult:
        """Activate a draft directive.

        Args:
            graph: Current graph.
            execution_id: Directive to activate.

        Returns:
            Updated graph and ``DirectiveActivated`` event.
        """
        directive = self._require(graph, execution_id)
        activated = directive.activate()
        new_graph = graph.replace_directive(activated)
        event = DirectiveActivated(
            **_event_meta(),
            execution_id=activated.id,
            lineage_id=activated.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def retire(self, graph: DirectiveGraph, execution_id: ExecutionId) -> LifecycleResult:
        """Retire an active directive (status → deprecated).

        Args:
            graph: Current graph.
            execution_id: Directive to retire.

        Returns:
            Updated graph and ``DirectiveRetired`` event.
        """
        directive = self._require(graph, execution_id)
        retired = directive.retire()
        new_graph = graph.replace_directive(retired)
        event = DirectiveRetired(
            **_event_meta(),
            execution_id=retired.id,
            lineage_id=retired.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def supersede(
        self,
        graph: DirectiveGraph,
        execution_id: ExecutionId,
        successor_id: ExecutionId,
    ) -> LifecycleResult:
        """Supersede an active directive with a successor.

        Args:
            graph: Current graph.
            execution_id: Directive being superseded.
            successor_id: Replacing directive (must exist and be active/draft).

        Returns:
            Updated graph and ``DirectiveSuperseded`` event.
        """
        directive = self._require(graph, execution_id)
        successor = self._require(graph, successor_id)
        if successor.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            raise LifecycleInvariantError(
                f"Successor {successor_id!r} must be active or draft "
                f"(got {successor.status!r})"
            )
        superseded = directive.supersede(successor_id)
        new_graph = graph.replace_directive(superseded)
        event = DirectiveSuperseded(
            **_event_meta(),
            execution_id=superseded.id,
            lineage_id=superseded.lineage_id,
            successor_id=successor_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def revise(
        self,
        graph: DirectiveGraph,
        execution_id: ExecutionId,
        revision: str,
        **field_updates: object,
    ) -> LifecycleResult:
        """Revise a directive (same identity; no lineage record required).

        Args:
            graph: Current graph.
            execution_id: Directive to revise.
            revision: New revision identifier.
            **field_updates: Optional non-identity field updates.

        Returns:
            Updated graph and ``DirectiveRevised`` event.
        """
        directive = self._require(graph, execution_id)
        revised = directive.with_revision(revision, **field_updates)
        new_graph = graph.replace_directive(revised)
        event = DirectiveRevised(
            **_event_meta(),
            execution_id=revised.id,
            lineage_id=revised.lineage_id,
            directive_revision=revision,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def rename(
        self,
        graph: DirectiveGraph,
        execution_id: ExecutionId,
        message: str,
    ) -> LifecycleResult:
        """Rename a directive message (identity unchanged).

        Args:
            graph: Current graph.
            execution_id: Directive to rename.
            message: New human-readable message.

        Returns:
            Updated graph and ``DirectiveRenamed`` event.
        """
        directive = self._require(graph, execution_id)
        renamed = directive.with_message(message)
        new_graph = graph.replace_directive(renamed)
        event = DirectiveRenamed(
            **_event_meta(),
            execution_id=renamed.id,
            lineage_id=renamed.lineage_id,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def fork(
        self,
        graph: DirectiveGraph,
        parent_execution_id: ExecutionId,
        child_execution_ids: tuple[ExecutionId, ExecutionId],
        timestamp: UtcTimestamp,
        reason: str | None = None,
    ) -> LifecycleResult:
        """Fork a parent into two new execution IDs sharing the lineage root.

        The parent is retired (deprecated). Children inherit ``lineage_id`` and
        receive ``lineage.operation=fork``.

        Args:
            graph: Current graph.
            parent_execution_id: Source directive.
            child_execution_ids: Two new unique execution IDs.
            timestamp: Operation timestamp (UTC).
            reason: Optional human-readable reason.

        Returns:
            Updated graph and ``DirectiveForked`` event.
        """
        parent = self._require(graph, parent_execution_id)
        if parent.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            raise InvalidLifecycleTransitionError(
                f"Cannot fork directive {parent_execution_id!r} with status {parent.status!r}"
            )
        if child_execution_ids[0] == child_execution_ids[1]:
            raise LifecycleInvariantError("Fork child execution IDs must be distinct")
        for cid in child_execution_ids:
            if cid in graph.execution_ids():
                raise LifecycleInvariantError(f"Execution ID already exists: {cid!r}")
            if cid == parent.id:
                raise LifecycleInvariantError("Fork child ID must not equal parent ID")

        lineage = Lineage(
            operation=LineageOperation.FORK,
            parent_lineage_ids=(parent.lineage_id,),
            parent_execution_ids=(parent.id,),
            timestamp=timestamp,
            reason=reason,
        )
        children = tuple(
            parent.model_copy(
                update={
                    "id": cid,
                    "lineage_id": parent.lineage_id,
                    "lineage": lineage,
                    "status": DirectiveStatus.DRAFT,
                    "created_at": timestamp,
                }
            )
            for cid in child_execution_ids
        )
        retired_parent = parent.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        new_graph = graph.with_directives(
            self._replace_and_append(graph.directives, retired_parent, children)
        )
        event = DirectiveForked(
            **_event_meta(),
            parent_execution_id=parent.id,
            lineage_id=parent.lineage_id,
            child_execution_ids=child_execution_ids,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    def merge(
        self,
        graph: DirectiveGraph,
        parent_a_id: ExecutionId,
        parent_b_id: ExecutionId,
        timestamp: UtcTimestamp,
        reason: str | None = None,
        merged_message: str | None = None,
    ) -> LifecycleResult:
        """Merge two directives into one new execution ID (SPEC §2.2.2).

        Both parents are deprecated. Surviving ``lineage_id`` is the
        lexicographic minimum of the parents' lineage IDs.

        Args:
            graph: Current graph.
            parent_a_id: First parent execution ID.
            parent_b_id: Second parent execution ID.
            timestamp: Operation timestamp (UTC).
            reason: Optional human-readable reason.
            merged_message: Optional message for the merged directive;
                defaults to parent A's message.

        Returns:
            Updated graph and ``DirectiveMerged`` event.
        """
        if parent_a_id == parent_b_id:
            raise LifecycleInvariantError("Cannot merge a directive with itself")
        parent_a = self._require(graph, parent_a_id)
        parent_b = self._require(graph, parent_b_id)
        for p in (parent_a, parent_b):
            if p.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
                raise InvalidLifecycleTransitionError(
                    f"Cannot merge directive {p.id!r} with status {p.status!r}"
                )

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
            timestamp,
        )
        if merged_id in graph.execution_ids():
            raise LifecycleInvariantError(f"Merge execution ID already exists: {merged_id!r}")

        lineage = Lineage(
            operation=LineageOperation.MERGE,
            parent_lineage_ids=sorted_lineage,
            parent_execution_ids=sorted_exec,
            timestamp=timestamp,
            reason=reason,
        )
        # Prefer content from the parent whose lineage root survives.
        base = parent_a if parent_a.lineage_id == surviving_lineage else parent_b
        merged = base.model_copy(
            update={
                "id": merged_id,
                "lineage_id": surviving_lineage,
                "lineage": lineage,
                "status": DirectiveStatus.DRAFT,
                "created_at": timestamp,
                "message": merged_message if merged_message is not None else base.message,
            }
        )
        retired_a = parent_a.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        retired_b = parent_b.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        replaced = {retired_a.id: retired_a, retired_b.id: retired_b}
        new_directives = (*(replaced.get(d.id, d) for d in graph.directives), merged)
        new_graph = graph.with_directives(new_directives)
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
        graph: DirectiveGraph,
        parent_execution_id: ExecutionId,
        child_execution_ids: tuple[ExecutionId, ...],
        timestamp: UtcTimestamp,
        reason: str | None = None,
    ) -> LifecycleResult:
        """Split a parent into multiple new execution IDs sharing the lineage root.

        Args:
            graph: Current graph.
            parent_execution_id: Source directive.
            child_execution_ids: Two or more new unique execution IDs.
            timestamp: Operation timestamp (UTC).
            reason: Optional human-readable reason.

        Returns:
            Updated graph and ``DirectiveSplit`` event.
        """
        parent = self._require(graph, parent_execution_id)
        if parent.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
            raise InvalidLifecycleTransitionError(
                f"Cannot split directive {parent_execution_id!r} with status {parent.status!r}"
            )
        if len(child_execution_ids) < 2:
            raise LifecycleInvariantError("Split requires at least 2 child execution IDs")
        if len(child_execution_ids) != len(set(child_execution_ids)):
            raise LifecycleInvariantError("Split child execution IDs must be unique")
        for cid in child_execution_ids:
            if cid in graph.execution_ids():
                raise LifecycleInvariantError(f"Execution ID already exists: {cid!r}")
            if cid == parent.id:
                raise LifecycleInvariantError("Split child ID must not equal parent ID")

        lineage = Lineage(
            operation=LineageOperation.SPLIT,
            parent_lineage_ids=(parent.lineage_id,),
            parent_execution_ids=(parent.id,),
            timestamp=timestamp,
            reason=reason,
        )
        children = tuple(
            parent.model_copy(
                update={
                    "id": cid,
                    "lineage_id": parent.lineage_id,
                    "lineage": lineage,
                    "status": DirectiveStatus.DRAFT,
                    "created_at": timestamp,
                }
            )
            for cid in child_execution_ids
        )
        retired_parent = parent.model_copy(update={"status": DirectiveStatus.DEPRECATED})
        new_graph = graph.with_directives(
            self._replace_and_append(graph.directives, retired_parent, children)
        )
        event = DirectiveSplit(
            **_event_meta(),
            parent_execution_id=parent.id,
            lineage_id=parent.lineage_id,
            child_execution_ids=child_execution_ids,
        )
        return LifecycleResult(graph=new_graph, events=(event,))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require(graph: DirectiveGraph, execution_id: ExecutionId) -> Directive:
        directive = graph.get_by_id(execution_id)
        if directive is None:
            raise DirectiveNotFoundError(execution_id)
        return directive

    @staticmethod
    def _replace_and_append(
        directives: tuple[Directive, ...],
        replacement: Directive,
        extras: tuple[Directive, ...],
    ) -> tuple[Directive, ...]:
        updated = tuple(replacement if d.id == replacement.id else d for d in directives)
        return updated + extras
