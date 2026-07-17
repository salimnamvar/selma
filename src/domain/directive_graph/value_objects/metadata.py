"""Metadata value objects — per-directive and dataset-level.

Domain-shaped only: unknown extension keys must already be folded into
``extensions`` by the anti-corruption layer before construction.

Reference: SPECIFICATION.md §7.1, §2.2.4
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.directive_graph.enums import LineagePreservation, SemanticWeightType
from domain.directive_graph.scalars import LineageId, UtcTimestamp
from domain.directive_graph.value_objects.audit import AuditTrail

# Pattern matches keys that would introduce executable logic into metadata.
# Per rule_schema.json patternProperties and SPECIFICATION.md §7.1.
_PROHIBITED_KEY_PATTERN: re.Pattern[str] = re.compile(r"^(x-exec|x-eval|x-hint|evaluator_|evaluator\.)")


def _check_extensions(extensions: dict[str, Any]) -> dict[str, Any]:
    """Raise ValueError if any extension key matches the prohibited pattern.

    Args:
        extensions: Extension key-value pairs to check.

    Returns:
        The unchanged extensions dict.

    Raises:
        ValueError: If any key matches the executable-hint prohibition pattern.
    """
    for key in extensions:
        if _PROHIBITED_KEY_PATTERN.match(key):
            raise ValueError(
                f"Metadata key {key!r} matches prohibited executable-hint pattern "
                f"(x-exec*, x-eval*, x-hint*, evaluator_*, evaluator.*)"
            )
    return extensions


class NonSurvivingParent(BaseModel):
    """A single non-surviving parent entry in a merge provenance record.

    Attributes:
        lineage_id: Lineage ID of the non-surviving parent.
        semantic_weight: Importance classification.
        context: What this parent contributed.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    lineage_id: LineageId
    semantic_weight: SemanticWeightType | None = None
    context: str | None = None


class MergeProvenance(BaseModel):
    """Documents non-surviving parent lineage IDs during a merge operation.

    Mitigates lexicographic-min provenance loss by capturing the semantic
    weight and context of each non-surviving parent.

    Attributes:
        non_surviving_parents: Non-surviving entries.
        merged_at: Timestamp of the merge.
        merge_notes: Additional context about the merge.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    non_surviving_parents: tuple[NonSurvivingParent, ...] = Field(min_length=1)
    merged_at: UtcTimestamp | None = None
    merge_notes: str | None = None


class MigrationInfo(BaseModel):
    """Records migration context and lineage handling.

    On a per-directive metadata object, ``superseded_by`` binds a superseded
    rule to its successor (SPECIFICATION.md §2.2.4).

    Attributes:
        superseded_by: Execution ID (or dataset version) that superseded this.
        migration_notes: Human-readable migration description.
        upgrade_from: Previous dataset version migrated from.
        upgrade_to: Target version for next migration.
        migration_required: Whether manual steps are needed.
        lineage_preservation: How lineage IDs are handled.
        merge_provenance: Non-surviving parent documentation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    superseded_by: str | None = None
    migration_notes: str | None = None
    upgrade_from: str | None = None
    upgrade_to: str | None = None
    migration_required: bool | None = None
    lineage_preservation: LineagePreservation | None = None
    merge_provenance: MergeProvenance | None = None


class DirectiveMetadata(BaseModel):
    """Per-directive metadata container.

    Informational only — MUST NOT contain executable hints.
    ``metadata.audit.authored_by`` is compiled to ``creator_provenance``
    for segregation enforcement (SPECIFICATION.md §3.2).

    Domain-shaped: arbitrary extension keys live only under ``extensions``.
    Wire-format scooping of unknown top-level keys is the ACL's job.

    Attributes:
        audit: Authorship and approval metadata.
        migration: Supersession / migration provenance.
        extensions: Arbitrary additional properties (contamination-guarded).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit: AuditTrail | None = None
    migration: MigrationInfo | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_no_executable_hints(self) -> DirectiveMetadata:
        """Reject any extension key matching the executable-hint prohibition.

        Raises:
            ValueError: If any extension key matches the prohibited pattern.
        """
        _check_extensions(self.extensions)
        return self


class DatasetMetadata(BaseModel):
    """Dataset-level metadata container.

    Informational only — MUST NOT contain executable hints.

    Domain-shaped: arbitrary extension keys live only under ``extensions``.

    Attributes:
        audit: Dataset-level audit trail.
        vendor: Vendor-specific string annotations.
        author: Author-specific string annotations.
        domain: Regulatory or business domain.
        jurisdiction: Legal or operational jurisdiction.
        project: Project identifier.
        migration: Migration provenance information.
        extensions: Arbitrary additional properties (contamination-guarded).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit: AuditTrail | None = None
    vendor: dict[str, str] | None = None
    author: dict[str, str] | None = None
    domain: str | None = None
    jurisdiction: str | None = None
    project: str | None = None
    migration: MigrationInfo | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_no_executable_hints(self) -> DatasetMetadata:
        """Reject any extension key matching the executable-hint prohibition.

        Raises:
            ValueError: If any extension key matches the prohibited pattern.
        """
        _check_extensions(self.extensions)
        return self
