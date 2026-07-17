"""Domain events for the Directive Graph bounded context.

Raised by lifecycle operations on the aggregate (fork, merge, split, retire,
activate, revise, rename, supersede).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from domain.shared.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class DirectiveActivated(DomainEvent):
    """A directive transitioned to active status."""

    event_type: ClassVar[str] = "directive.activated"
    execution_id: str
    lineage_id: str


@dataclass(frozen=True, kw_only=True)
class DirectiveRetired(DomainEvent):
    """A directive was retired (status → deprecated)."""

    event_type: ClassVar[str] = "directive.retired"
    execution_id: str
    lineage_id: str


@dataclass(frozen=True, kw_only=True)
class DirectiveSuperseded(DomainEvent):
    """A directive was superseded by another execution ID."""

    event_type: ClassVar[str] = "directive.superseded"
    execution_id: str
    lineage_id: str
    successor_id: str


@dataclass(frozen=True, kw_only=True)
class DirectiveRevised(DomainEvent):
    """A directive was revised (same identity, new revision)."""

    event_type: ClassVar[str] = "directive.revised"
    execution_id: str
    lineage_id: str
    directive_revision: str | None


@dataclass(frozen=True, kw_only=True)
class DirectiveRenamed(DomainEvent):
    """A directive message/label was renamed (identity unchanged)."""

    event_type: ClassVar[str] = "directive.renamed"
    execution_id: str
    lineage_id: str


@dataclass(frozen=True, kw_only=True)
class DirectiveForked(DomainEvent):
    """A directive was forked into two new execution IDs."""

    event_type: ClassVar[str] = "directive.forked"
    parent_execution_id: str
    lineage_id: str
    child_execution_ids: tuple[str, str]


@dataclass(frozen=True, kw_only=True)
class DirectiveMerged(DomainEvent):
    """Two directives were merged into one new execution ID."""

    event_type: ClassVar[str] = "directive.merged"
    parent_execution_ids: tuple[str, str]
    parent_lineage_ids: tuple[str, str]
    merged_execution_id: str
    merged_lineage_id: str


@dataclass(frozen=True, kw_only=True)
class DirectiveSplit(DomainEvent):
    """A directive was split into multiple new execution IDs."""

    event_type: ClassVar[str] = "directive.split"
    parent_execution_id: str
    lineage_id: str
    child_execution_ids: tuple[str, ...]
