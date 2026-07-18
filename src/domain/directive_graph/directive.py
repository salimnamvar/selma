"""Directive entity — core business object of the Directive Graph.

The ``Directive`` is the single entity inside the ``DirectiveGraph`` aggregate.
It has dual identity (``lineage_id`` + ``id``), a defined lifecycle, and owns
its evaluation contract.

Domain shape only: wire-format normalisation (``evaluator_type`` merge, etc.)
is performed by the anti-corruption layer before construction.

Reference: SPECIFICATION.md §2.2, §2.2.4
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from domain.directive_graph.enums import DeonticType
from domain.directive_graph.enums import DirectiveStatus
from domain.directive_graph.enums import EvaluatorType
from domain.directive_graph.enums import PriorityLevel
from domain.directive_graph.enums import SeverityWeight
from domain.directive_graph.evaluators import Evaluator
from domain.directive_graph.exceptions import InvalidLifecycleTransitionError
from domain.directive_graph.scalars import AnchorReference
from domain.directive_graph.scalars import DirectiveReference
from domain.directive_graph.scalars import ExecutionId
from domain.directive_graph.scalars import LineageId
from domain.directive_graph.scalars import UtcTimestamp
from domain.directive_graph.value_objects.conflict_resolution import ConflictResolution
from domain.directive_graph.value_objects.lineage import Lineage
from domain.directive_graph.value_objects.metadata import DirectiveMetadata
from domain.directive_graph.value_objects.metadata import MigrationInfo
from domain.directive_graph.value_objects.scope import Scope


class Directive(BaseModel):
    """A single regulatory or business directive with dual identity.

    Identity
    --------
    Composite: ``(lineage_id, id)``.
    ``lineage_id`` is the immutable conceptual root.
    ``id`` (execution ID) may change on fork / merge / split.

    Lifecycle
    ---------
    ``draft`` → ``active`` → ``deprecated`` / ``superseded``.
    Prefer lifecycle methods (``activate``, ``retire``, ``supersede``) over
    raw field assignment.

    Attributes:
        lineage_id: Immutable root identity.
        id: Active execution identity.
        type: Deontic force (obligation / prohibition / permission).
        message: Human-readable directive text.
        status: Current lifecycle state.
        evaluator_config: Polymorphic evaluation logic (domain-shaped).
        created_at: Creation timestamp (immutable).
        scope: Structured applicability context.
        priority: Authority rank; defaults to ``operational``.
        weight: Violation severity classification.
        conflict_resolution: Explicit conflict override.
        lineage: Lineage operation record (fork/merge/split only).
        depends_on: IDs of directives evaluated first.
        conflicts_with: IDs of conflicting directives.
        metadata: Informational metadata.
        expires_at: Optional expiry timestamp.
        anchor_ref: Link to policy document.
        directive_revision: Revision identifier (e.g. ``"v3"``).
        control_version: Evaluation-logic version string.
        rationale: Why this directive exists.
        remediation: Corrective action description.
        parameters: Optional free-form parameter bag (schema escape hatch).
        target: Deprecated bare target string; prefer ``scope``.
    """

    model_config = ConfigDict(extra="forbid")

    # --- Required identity and classification fields ---
    lineage_id: LineageId
    id: ExecutionId
    type: DeonticType
    message: str = Field(min_length=1)
    status: DirectiveStatus
    evaluator_config: Evaluator
    created_at: UtcTimestamp

    # --- Optional fields with defaults ---
    priority: PriorityLevel = PriorityLevel.OPERATIONAL

    # --- Optional fields without defaults ---
    scope: Scope | None = None
    weight: SeverityWeight | None = None
    conflict_resolution: ConflictResolution | None = None
    lineage: Lineage | None = None
    depends_on: list[DirectiveReference] = Field(default_factory=list)
    conflicts_with: list[DirectiveReference] = Field(default_factory=list)
    metadata: DirectiveMetadata | None = None
    expires_at: UtcTimestamp | None = None
    anchor_ref: AnchorReference | None = None
    directive_revision: str | None = None
    control_version: str | None = None
    rationale: str | None = None
    remediation: str | None = None
    parameters: dict[str, Any] | None = None
    target: str | None = None  # deprecated; prefer scope

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    @field_validator("depends_on", "conflicts_with", mode="after")
    @classmethod
    def _validate_unique_references(cls, a_values: list[DirectiveReference]) -> list[DirectiveReference]:
        """Ensure reference lists contain no duplicate IDs.

        Args:
            a_values: The reference list.

        Returns:
            The unchanged list if unique.

        Raises:
            ValueError: If duplicate IDs are found.
        """
        if len(a_values) != len(set(a_values)):
            seen: set[str] = set()
            dups = [v for v in a_values if v in seen or seen.add(v)]  # type: ignore[func-returns-value]
            msg = f"Duplicate directive references: {dups}"
            raise ValueError(msg)
        return a_values

    # ------------------------------------------------------------------
    # Cross-field invariants
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_active_directive_has_author(self) -> Directive:
        """Enforce that active directives have authored_by set.

        Raises:
            ValueError: If status is ACTIVE and authored_by is absent.
        """
        if self.status == DirectiveStatus.ACTIVE:
            authored_by = self.metadata and self.metadata.audit and self.metadata.audit.authored_by
            if not authored_by:
                msg = "Active directives require metadata.audit.authored_by to be set"
                raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_expires_after_created(self) -> Directive:
        """Enforce that expires_at is strictly after created_at.

        Uses lexicographic comparison, which is correct for UTC-only ISO 8601
        timestamps (``YYYY-MM-DDTHH:MM:SS[.sss]Z`` sorts correctly as strings).

        Raises:
            ValueError: If expires_at is not strictly after created_at.
        """
        if self.expires_at is not None and self.expires_at <= self.created_at:
            msg = f"expires_at ({self.expires_at!r}) must be strictly after created_at ({self.created_at!r})"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_superseded_has_successor(self) -> Directive:
        """Enforce that superseded directives declare a successor id.

        Raises:
            ValueError: If status is SUPERSEDED without migration.superseded_by.
        """
        if self.status == DirectiveStatus.SUPERSEDED:
            successor = self.metadata and self.metadata.migration and self.metadata.migration.superseded_by
            if not successor:
                msg = "Superseded directives require metadata.migration.superseded_by to be set"
                raise ValueError(msg)
        return self

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def evaluator_type(self) -> EvaluatorType:
        """Return the evaluator type from the config discriminator.

        Returns:
            The type of this directive's evaluator.
        """
        return EvaluatorType(self.evaluator_config.evaluator_type)

    @property
    def is_active_for_resolution(self) -> bool:
        """Return True if this directive participates as an active resolution target.

        Draft compiles as active per SPECIFICATION.md §2.8.1 / §2.15.
        """
        return self.status in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT)

    # ------------------------------------------------------------------
    # Lifecycle methods (return new instances)
    # ------------------------------------------------------------------

    def activate(self) -> Directive:
        """Transition draft → active.

        Returns:
            A new Directive with status ACTIVE.

        Raises:
            InvalidLifecycleTransitionError: If current status is not DRAFT or
                authored_by is missing.
        """
        if self.status != DirectiveStatus.DRAFT:
            msg = f"Cannot activate directive {self.id!r} from status {self.status!r}; expected 'draft'"
            raise InvalidLifecycleTransitionError(msg)
        authored_by = self.metadata and self.metadata.audit and self.metadata.audit.authored_by
        if not authored_by:
            msg = f"Cannot activate directive {self.id!r}: metadata.audit.authored_by is required"
            raise InvalidLifecycleTransitionError(msg)
        return self.model_copy(update={"status": DirectiveStatus.ACTIVE})

    def retire(self) -> Directive:
        """Transition active → deprecated (retire).

        Returns:
            A new Directive with status DEPRECATED.

        Raises:
            InvalidLifecycleTransitionError: If current status is not ACTIVE.
        """
        if self.status != DirectiveStatus.ACTIVE:
            msg = f"Cannot retire directive {self.id!r} from status {self.status!r}; expected 'active'"
            raise InvalidLifecycleTransitionError(msg)
        return self.model_copy(update={"status": DirectiveStatus.DEPRECATED})

    def supersede(self, a_successor_id: ExecutionId) -> Directive:
        """Transition active → superseded with a successor binding.

        Args:
            a_successor_id: Execution ID of the replacing directive.

        Returns:
            A new Directive with status SUPERSEDED and migration.superseded_by set.

        Raises:
            InvalidLifecycleTransitionError: If current status is not ACTIVE.
        """
        if self.status != DirectiveStatus.ACTIVE:
            msg = f"Cannot supersede directive {self.id!r} from status {self.status!r}; expected 'active'"
            raise InvalidLifecycleTransitionError(msg)
        migration = MigrationInfo(superseded_by=a_successor_id)
        if self.metadata is None:
            new_meta = DirectiveMetadata(migration=migration)
        else:
            new_meta = self.metadata.model_copy(update={"migration": migration})
        return self.model_copy(update={"status": DirectiveStatus.SUPERSEDED, "metadata": new_meta})

    def with_message(self, a_message: str) -> Directive:
        """Return a copy with an updated human-readable message (rename).

        Args:
            a_message: Non-empty directive text.

        Returns:
            A new Directive with the updated message.
        """
        if not a_message:
            msg = "message must be non-empty"
            raise ValueError(msg)
        return self.model_copy(update={"message": a_message})

    def with_revision(self, a_revision: str, **a_field_updates: Any) -> Directive:
        """Return a revised copy (same identity; lineage field not required).

        Args:
            a_revision: New directive_revision value.
            **a_field_updates: Optional additional field updates (not identity).

        Returns:
            A new Directive with updated revision and optional fields.

        Raises:
            ValueError: If identity fields are included in field_updates.
        """
        forbidden = {"lineage_id", "id", "status"}
        bad = forbidden.intersection(a_field_updates)
        if bad:
            msg = f"Revision must not change identity/status fields: {sorted(bad)}"
            raise ValueError(msg)
        updates = dict(a_field_updates)
        updates["directive_revision"] = a_revision
        return self.model_copy(update=updates)
