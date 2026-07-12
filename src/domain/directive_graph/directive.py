"""Directive entity — core business object of the Directive Graph.

The ``Directive`` is the single entity inside the ``DirectiveGraph`` aggregate.
It has dual identity (``lineage_id`` + ``id``), a defined lifecycle, and owns
its evaluation contract.

JSON format mapping
-------------------
The JSON Schema separates ``evaluator_type`` (at directive level) from
``evaluator_config`` (the config object).  A ``model_validator(mode="before")``
merges them so that the domain field ``evaluator_config: Evaluator`` is a
fully self-contained discriminated union value.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.2, §3
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.directive_graph.enums import (
    DirectiveStatus,
    DeonticType,
    EvaluatorType,
    PriorityLevel,
    SeverityWeight,
)
from domain.directive_graph.evaluators import Evaluator
from domain.directive_graph.scalars import (
    AnchorReference,
    DirectiveReference,
    ExecutionId,
    LineageId,
    UtcTimestamp,
)
from domain.directive_graph.value_objects.conflict_resolution import ConflictResolution
from domain.directive_graph.value_objects.lineage import Lineage
from domain.directive_graph.value_objects.metadata import DirectiveMetadata
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

    Mutation
    --------
    This model is **not** frozen.  Use ``directive.model_copy(update={...})``
    for mutations; never assign fields directly.

    Attributes:
        lineage_id (LineageId): Immutable root identity.
        id (ExecutionId): Active execution identity.
        type (DeonticType): Deontic force (obligation / prohibition / permission).
        message (str): Human-readable directive text.
        status (DirectiveStatus): Current lifecycle state.
        evaluator_config (Evaluator): Polymorphic evaluation logic.
        created_at (UtcTimestamp): Creation timestamp (immutable).
        scope (Scope | None): Structured applicability context.
        priority (PriorityLevel): Authority rank; defaults to ``operational``.
        weight (SeverityWeight | None): Violation severity classification.
        conflict_resolution (ConflictResolution | None): Explicit conflict override.
        lineage (Lineage | None): Lineage operation record (fork/merge/split only).
        depends_on (list[DirectiveReference]): IDs of directives evaluated first.
        conflicts_with (list[DirectiveReference]): IDs of conflicting directives.
        metadata (DirectiveMetadata | None): Informational metadata.
        expires_at (UtcTimestamp | None): Optional expiry timestamp.
        anchor_ref (AnchorReference | None): Link to policy document.
        directive_revision (str | None): Revision identifier (e.g. ``"v3"``).
        control_version (str | None): Evaluation-logic version string.
        rationale (str | None): Why this directive exists.
        remediation (str | None): Corrective action description.
        parameters (dict[str, Any] | None): Evaluator configuration parameters.
        target (str | None): Deprecated bare target string.
    """

    model_config = ConfigDict(extra="forbid")

    # --- Required identity and classification fields ---
    lineage_id: LineageId
    id: ExecutionId  # noqa: A003  (shadows builtin; intentional schema alignment)
    type: DeonticType  # noqa: A003  (shadows builtin; intentional schema alignment)
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
    # Parsing normalisation
    # ------------------------------------------------------------------

    @model_validator(mode="before")
    @classmethod
    def _merge_evaluator_type_into_config(cls, data: Any) -> Any:
        """Merge top-level ``evaluator_type`` into ``evaluator_config``.

        The JSON Schema stores ``evaluator_type`` as a separate directive-level
        field and ``evaluator_config`` as the config object without a type tag.
        This validator injects ``evaluator_type`` into the config dict so the
        discriminated union on ``evaluator_config`` can route correctly.

        Args:
            data (Any): Raw input dictionary.

        Returns:
            Any: Transformed data with evaluator_type embedded in evaluator_config.
        """
        if not isinstance(data, dict):
            return data
        ev_type = data.get("evaluator_type")
        ev_config = data.get("evaluator_config")
        if (
            ev_type is not None
            and isinstance(ev_config, dict)
            and "evaluator_type" not in ev_config
        ):
            data = dict(data)
            data["evaluator_config"] = {"evaluator_type": ev_type, **ev_config}
            del data["evaluator_type"]
        return data

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    @field_validator("depends_on", "conflicts_with", mode="after")
    @classmethod
    def _validate_unique_references(cls, values: list[DirectiveReference]) -> list[DirectiveReference]:
        """Ensure reference lists contain no duplicate IDs.

        Args:
            values (list[DirectiveReference]): The reference list.

        Returns:
            list[DirectiveReference]: The unchanged list if unique.

        Raises:
            ValueError: If duplicate IDs are found.
        """
        if len(values) != len(set(values)):
            seen: set[str] = set()
            dups = [v for v in values if v in seen or seen.add(v)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate directive references: {dups}")
        return values

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
            authored_by = (
                self.metadata
                and self.metadata.audit
                and self.metadata.audit.authored_by
            )
            if not authored_by:
                raise ValueError(
                    "Active directives require metadata.audit.authored_by to be set"
                )
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
            raise ValueError(
                f"expires_at ({self.expires_at!r}) must be strictly after "
                f"created_at ({self.created_at!r})"
            )
        return self

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    @property
    def evaluator_type(self) -> EvaluatorType:
        """Return the evaluator type from the config discriminator.

        Returns:
            EvaluatorType: The type of this directive's evaluator.
        """
        return EvaluatorType(self.evaluator_config.evaluator_type)
