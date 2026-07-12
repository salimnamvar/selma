"""Metadata value objects — per-directive and dataset-level.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.3
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from domain.directive_graph.enums import LineagePreservation
from domain.directive_graph.enums import SemanticWeightType
from domain.directive_graph.scalars import LineageId
from domain.directive_graph.scalars import UtcTimestamp
from domain.directive_graph.value_objects.audit import AuditTrail

# Pattern matches keys that would introduce executable logic into metadata.
# Per rule_schema.json patternProperties and SPECIFICATION.md §7.1.
_PROHIBITED_KEY_PATTERN: re.Pattern[str] = re.compile(r"^(x-exec|x-eval|x-hint|evaluator_|evaluator\.)")


def _check_extensions(extensions: dict[str, Any]) -> dict[str, Any]:
    """Raise ValueError if any extension key matches the prohibited pattern.

    Args:
        extensions (dict[str, Any]): Extension key-value pairs to check.

    Returns:
        dict[str, Any]: The unchanged extensions dict.

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
        lineage_id (LineageId): Lineage ID of the non-surviving parent.
        semantic_weight (SemanticWeightType | None): Importance classification.
        context (str | None): What this parent contributed.
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
        non_surviving_parents (tuple[NonSurvivingParent, ...]): Non-surviving entries.
        merged_at (UtcTimestamp | None): Timestamp of the merge.
        merge_notes (str | None): Additional context about the merge.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    non_surviving_parents: tuple[NonSurvivingParent, ...] = Field(min_length=1)
    merged_at: UtcTimestamp | None = None
    merge_notes: str | None = None


class MigrationInfo(BaseModel):
    """Records dataset migration context and lineage handling.

    Attributes:
        superseded_by (str | None): Version that superseded this dataset.
        migration_notes (str | None): Human-readable migration description.
        upgrade_from (str | None): Previous dataset version migrated from.
        upgrade_to (str | None): Target version for next migration.
        migration_required (bool | None): Whether manual steps are needed.
        lineage_preservation (LineagePreservation | None): How lineage IDs are handled.
        merge_provenance (MergeProvenance | None): Non-surviving parent documentation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    superseded_by: str | None = None
    migration_notes: str | None = None
    upgrade_from: str | None = None
    upgrade_to: str | None = None
    migration_required: bool | None = None
    lineage_preservation: LineagePreservation | None = None
    merge_provenance: MergeProvenance | None = None


# Keys explicitly defined as named fields on DirectiveMetadata.
_DIRECTIVE_METADATA_KNOWN_KEYS: frozenset[str] = frozenset({"audit", "extensions"})


class DirectiveMetadata(BaseModel):
    """Per-directive metadata container.

    Informational only — MUST NOT contain executable hints.
    ``metadata.audit.authored_by`` is compiled to ``creator_provenance``
    for segregation enforcement (SPECIFICATION.md §3.2).

    The JSON Schema allows arbitrary additional properties on the metadata
    object (``additionalProperties: true``).  Any top-level key that is not
    a named field is collected into ``extensions`` by the before-validator.

    Attributes:
        audit (AuditTrail | None): Authorship and approval metadata.
        extensions (dict[str, Any]): Arbitrary additional properties
            (contamination-guarded).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit: AuditTrail | None = None
    extensions: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _collect_unknown_keys(cls, data: Any) -> Any:
        """Collect unrecognised top-level metadata keys into ``extensions``.

        The JSON Schema uses ``additionalProperties: true`` on the metadata
        object; unknown keys arrive as top-level keys in the raw dict and
        must be routed to the ``extensions`` field so that Pydantic's
        ``extra='forbid'`` constraint is not violated.

        Args:
            data (Any): Raw input dictionary.

        Returns:
            Any: Normalised dict with unknown keys folded into ``extensions``.
        """
        if not isinstance(data, dict):
            return data
        unknowns = {k: v for k, v in data.items() if k not in _DIRECTIVE_METADATA_KNOWN_KEYS}
        if unknowns:
            data = dict(data)
            existing = data.get("extensions") or {}
            data["extensions"] = {**unknowns, **(existing if isinstance(existing, dict) else {})}
            for k in unknowns:
                del data[k]
        return data

    @model_validator(mode="after")
    def _check_no_executable_hints(self) -> DirectiveMetadata:
        """Reject any extension key matching the executable-hint prohibition.

        Raises:
            ValueError: If any extension key matches the prohibited pattern.
        """
        _check_extensions(self.extensions)
        return self


# Keys explicitly defined as named fields on DatasetMetadata.
_DATASET_METADATA_KNOWN_KEYS: frozenset[str] = frozenset(
    {"audit", "vendor", "author", "migration", "domain", "jurisdiction", "project", "extensions"}
)


class DatasetMetadata(BaseModel):
    """Dataset-level metadata container.

    Informational only — MUST NOT contain executable hints.

    The JSON Schema allows arbitrary additional properties on the metadata
    object (``additionalProperties: true``).  Any top-level key that is not
    a named field is collected into ``extensions`` by the before-validator.

    Attributes:
        audit (AuditTrail | None): Dataset-level audit trail.
        vendor (dict[str, str] | None): Vendor-specific string annotations.
        author (dict[str, str] | None): Author-specific string annotations.
        domain (str | None): Regulatory or business domain.
        jurisdiction (str | None): Legal or operational jurisdiction.
        project (str | None): Project identifier.
        migration (MigrationInfo | None): Migration provenance information.
        extensions (dict[str, Any]): Arbitrary additional properties
            (contamination-guarded).
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

    @model_validator(mode="before")
    @classmethod
    def _collect_unknown_keys(cls, data: Any) -> Any:
        """Collect unrecognised top-level metadata keys into ``extensions``.

        Args:
            data (Any): Raw input dictionary.

        Returns:
            Any: Normalised dict with unknown keys folded into ``extensions``.
        """
        if not isinstance(data, dict):
            return data
        unknowns = {k: v for k, v in data.items() if k not in _DATASET_METADATA_KNOWN_KEYS}
        if unknowns:
            data = dict(data)
            existing = data.get("extensions") or {}
            data["extensions"] = {**unknowns, **(existing if isinstance(existing, dict) else {})}
            for k in unknowns:
                del data[k]
        return data

    @model_validator(mode="after")
    def _check_no_executable_hints(self) -> DatasetMetadata:
        """Reject any extension key matching the executable-hint prohibition.

        Raises:
            ValueError: If any extension key matches the prohibited pattern.
        """
        _check_extensions(self.extensions)
        return self
