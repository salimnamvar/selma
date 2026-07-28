"""Pydantic v2 models for rule_schema.json.

Machine-executable rule structure. Contains the structural projection
of spec invariants — evaluator logic, identity, lineage, conflict resolution.

Schema contract: schema/rule_schema.json
Normative source: SPECIFICATION.md 8.2.4

These models are language-agnostic. Language-specific evaluator types
(e.g. ast_walk for Python) are handled as extension configs passed
through the evaluator_config's additionalProperties.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity

# ─── Schema-Specific Enums ───────────────────────────────────────────────────
# These are schema/infrastructure enums, not core domain concepts.


class EvaluatorType(StrEnum):
    """Pure evaluator types (language-agnostic).

    Language-specific extensions (e.g. ast_walk for Python) are handled
    via additional evaluator configs passed through the engine.
    """

    REGEX = "regex"
    FIELD_CHECK = "field_check"
    THRESHOLD = "threshold"
    COMPOSITE = "composite"


class ComparisonOperator(StrEnum):
    """Comparison operators for field_check and threshold evaluators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    MATCHES = "matches"


class ThresholdOperator(StrEnum):
    """Operators for threshold comparisons."""

    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class LogicOp(StrEnum):
    """Logical operators for composite evaluators."""

    AND = "and"
    OR = "or"
    NOT = "not"


class ConflictStrategy(StrEnum):
    """Conflict resolution strategies."""

    ALWAYS_WINS = "always_wins"
    NEVER_WINS = "never_wins"
    DEFER_TO = "defer_to"


class LineageOperation(StrEnum):
    """Identity lifecycle operations."""

    FORK = "fork"
    MERGE = "merge"
    SPLIT = "split"


class TargetType(StrEnum):
    """Scope target types."""

    TEXT = "text"
    STRUCTURED = "structured"
    BINARY = "binary"
    ANY = "any"


class FilterOperator(StrEnum):
    """Scope filter operators."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    SUBSET = "subset"


class LineagePreservation(StrEnum):
    """How lineage IDs are handled during migration."""

    IDENTITY_PRESERVED = "identity_preserved"
    IDENTITY_REASSIGNED = "identity_reassigned"
    REQUIRES_REMAP = "requires_remap"


# ─── Evaluator Configs (Discriminated Union) ─────────────────────────────────


class RegexEvaluatorConfig(BaseModel):
    """Regex evaluator config — matches text patterns."""

    model_config = ConfigDict(frozen=True)

    pattern: str = Field(
        min_length=1, max_length=4096, description="RE2-compatible regex pattern"
    )
    flags: str = Field(default="", pattern="^[ims]*$", description="Regex flags")


class FieldCheckEvaluatorConfig(BaseModel):
    """Field check evaluator config — compares field values."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(min_length=1, description="Field path to check")
    operator: ComparisonOperator = Field(description="Comparison operator")
    value: Any = Field(description="Value to compare against")


class ThresholdEvaluatorConfig(BaseModel):
    """Threshold evaluator config — numeric comparisons."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(min_length=1, description="Field path to check")
    operator: ThresholdOperator = Field(description="Threshold operator")
    threshold: float = Field(description="Finite IEEE 754 double")


class CompositeEvaluatorConfig(BaseModel):
    """Composite evaluator config — logical combinations."""

    model_config = ConfigDict(frozen=True)

    logic: LogicOp = Field(description="Logical operator")
    sub_evaluators: tuple[EvaluatorConfigEntry, ...] = Field(
        min_length=1,
        max_length=64,
        description="Sub-evaluators",
    )


class EvaluatorConfigEntry(BaseModel):
    """A sub-evaluator entry within a composite evaluator.

    Wraps evaluator_type + evaluator_config as a tagged union.
    """

    model_config = ConfigDict(frozen=True)

    evaluator_type: EvaluatorType = Field(description="Evaluator type discriminator")
    evaluator_config: (
        RegexEvaluatorConfig
        | FieldCheckEvaluatorConfig
        | ThresholdEvaluatorConfig
        | CompositeEvaluatorConfig
    ) = Field(description="Evaluator configuration")


# Rebuild to resolve forward reference
CompositeEvaluatorConfig.model_rebuild()


# ─── Typed Evaluator Config (discriminated by evaluator_type) ────────────────


class RegexEvaluator(BaseModel):
    """Regex evaluator — matches text patterns."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[EvaluatorType.REGEX] = Field(default=EvaluatorType.REGEX)
    evaluator_config: RegexEvaluatorConfig


class FieldCheckEvaluator(BaseModel):
    """Field check evaluator — compares field values."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[EvaluatorType.FIELD_CHECK] = Field(
        default=EvaluatorType.FIELD_CHECK
    )
    evaluator_config: FieldCheckEvaluatorConfig


class ThresholdEvaluator(BaseModel):
    """Threshold evaluator — numeric comparisons."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[EvaluatorType.THRESHOLD] = Field(
        default=EvaluatorType.THRESHOLD
    )
    evaluator_config: ThresholdEvaluatorConfig


class CompositeEvaluator(BaseModel):
    """Composite evaluator — logical combinations."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[EvaluatorType.COMPOSITE] = Field(
        default=EvaluatorType.COMPOSITE
    )
    evaluator_config: CompositeEvaluatorConfig


TypedEvaluator = Annotated[
    RegexEvaluator | FieldCheckEvaluator | ThresholdEvaluator | CompositeEvaluator,
    Field(discriminator="evaluator_type"),
]


# ─── Scope ───────────────────────────────────────────────────────────────────


class ScopeFilter(BaseModel):
    """A single applicability filter predicate."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(description="Path within target metadata or content")
    operator: FilterOperator = Field(description="Comparison operator")
    value: Any = Field(description="Value to compare against")


class Scope(BaseModel):
    """Structured applicability context."""

    model_config = ConfigDict(frozen=True)

    target_type: TargetType = Field(default=TargetType.ANY)
    domain: str = Field(default="", description="Regulatory or business domain")
    jurisdiction: str = Field(
        default="", description="Legal or operational jurisdiction"
    )
    filters: tuple[ScopeFilter, ...] = Field(default_factory=tuple)


# ─── Metadata ────────────────────────────────────────────────────────────────


class AuditMetadata(BaseModel):
    """Audit metadata for a rule."""

    model_config = ConfigDict(frozen=True)

    authored_by: str = Field(default="", description="Actor ID of directive creator")
    approved_by: str = Field(default="", description="Actor ID of approver")
    approved_at: str = Field(default="", description="Approval timestamp (UTC)")


class RuleMetadata(BaseModel):
    """Per-rule metadata. Informational only."""

    model_config = ConfigDict(frozen=True, extra="allow")

    audit: AuditMetadata = Field(default_factory=AuditMetadata)


# ─── Conflict Resolution ─────────────────────────────────────────────────────


class ConflictResolution(BaseModel):
    """Explicit conflict resolution override."""

    model_config = ConfigDict(frozen=True)

    strategy: ConflictStrategy = Field(description="Resolution strategy")
    defer_to: str | None = Field(default=None, description="Rule ID to defer to")

    @field_validator("defer_to")
    @classmethod
    def validate_defer_to(cls, v: str | None, info: Any) -> str | None:
        """defer_to is required when strategy is defer_to."""
        if info.data.get("strategy") == ConflictStrategy.DEFER_TO and not v:
            msg = "defer_to is required when strategy is defer_to"
            raise ValueError(msg)
        return v


# ─── Lineage ─────────────────────────────────────────────────────────────────


class Lineage(BaseModel):
    """Tracks identity lifecycle operations."""

    model_config = ConfigDict(frozen=True)

    operation: LineageOperation = Field(description="Lifecycle operation")
    parent_lineage_ids: tuple[str, ...] = Field(
        min_length=1, description="Parent lineage IDs"
    )
    parent_execution_ids: tuple[str, ...] = Field(
        min_length=1, description="Parent execution IDs"
    )
    timestamp: str = Field(description="Operation timestamp (UTC)")
    reason: str = Field(default="", description="Why this operation was performed")


# ─── Rule ────────────────────────────────────────────────────────────────────


class Rule(BaseModel):
    """A single machine-executable rule.

    Language-agnostic. The evaluator_type and evaluator_config define
    what this rule checks. Language-specific extensions are passed as
    additional evaluator configs through the engine.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    lineage_id: str = Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+[A-Z]?$",
        description="Immutable root identifier",
    )
    id: str = Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+[A-Z]?(-[A-Z0-9]+)*$",
        description="Active execution identifier",
    )

    # Deontic
    type: DeonticType = Field(description="Deontic classification")
    message: str = Field(min_length=1, description="Human-readable output")

    # Evaluator
    evaluator_type: EvaluatorType = Field(description="Evaluator type discriminator")
    evaluator_config: dict[str, Any] = Field(description="Evaluator configuration")

    # Lifecycle
    status: RuleStatus = Field(description="Lifecycle state")
    created_at: str = Field(description="Creation timestamp (UTC)")

    # Optional fields
    target: str = Field(default="", description="Deprecated: use scope")
    scope: Scope | None = Field(default=None)
    anchor_ref: str = Field(default="", description="Link to policy document")
    directive_revision: str = Field(default="")
    control_version: str = Field(default="")
    metadata: RuleMetadata = Field(default_factory=RuleMetadata)
    weight: Severity = Field(default=Severity.MEDIUM)
    priority: PriorityLevel = Field(default=PriorityLevel.OPERATIONAL)
    depends_on: tuple[str, ...] = Field(default_factory=tuple)
    conflicts_with: tuple[str, ...] = Field(default_factory=tuple)
    conflict_resolution: ConflictResolution | None = Field(default=None)
    expires_at: str = Field(default="")
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str = Field(default="")
    remediation: str = Field(default="")
    lineage: Lineage | None = Field(default=None)

    @property
    def rule_id(self) -> str:
        """Get the lineage ID (immutable root)."""
        return self.lineage_id

    def is_active(self) -> bool:
        """Check if this rule is active."""
        return self.status == RuleStatus.ACTIVE


# ─── Audit Metadata (Dataset-level) ──────────────────────────────────────────


class MergeProvenanceParent(BaseModel):
    """Non-surviving parent in a merge operation."""

    model_config = ConfigDict(frozen=True)

    lineage_id: str = Field(description="Non-surviving parent lineage_id")
    semantic_weight: str = Field(default="informational")
    context: str = Field(default="")


class MergeProvenance(BaseModel):
    """Merge provenance tracking."""

    model_config = ConfigDict(frozen=True)

    non_surviving_parents: tuple[MergeProvenanceParent, ...] = Field(min_length=1)
    merged_at: str = Field(default="")
    merge_notes: str = Field(default="")


class MigrationMetadata(BaseModel):
    """Migration metadata for a rule dataset."""

    model_config = ConfigDict(frozen=True)

    superseded_by: str = Field(default="")
    migration_notes: str = Field(default="")
    upgrade_from: str = Field(default="")
    upgrade_to: str = Field(default="")
    migration_required: bool = Field(default=False)
    lineage_preservation: LineagePreservation | None = Field(default=None)
    merge_provenance: MergeProvenance | None = Field(default=None)


class DatasetAuditMetadata(BaseModel):
    """Dataset-level audit metadata."""

    model_config = ConfigDict(frozen=True)

    authored_by: str = Field(default="")
    approved_by: str = Field(default="")
    approved_at: str = Field(default="")


class DatasetMetadata(BaseModel):
    """Dataset-level metadata. Informational only."""

    model_config = ConfigDict(frozen=True, extra="allow")

    audit: DatasetAuditMetadata = Field(default_factory=DatasetAuditMetadata)
    vendor: dict[str, str] = Field(default_factory=dict)
    author: dict[str, str] = Field(default_factory=dict)
    migration: MigrationMetadata | None = Field(default=None)
    domain: str = Field(default="")
    jurisdiction: str = Field(default="")
    project: str = Field(default="")


# ─── Rule Dataset (top-level) ────────────────────────────────────────────────


class RuleDataset(BaseModel):
    """A wrapped rule dataset — the top-level document.

    Contains version info, policy contract binding, and the list of rules.
    This is the machine-executable governance layer.
    """

    model_config = ConfigDict(frozen=True)

    version: str = Field(
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
        description="Directive graph version (semantic version)",
    )
    policy_contract_version: str = Field(
        pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$",
        description="Version of the paired policy_doctrine.yaml",
    )
    policy_contract_id: str = Field(
        default="universal-policy-doctrine",
        description="Identifier of the paired policy contract",
    )
    metadata: DatasetMetadata = Field(default_factory=DatasetMetadata)
    rules: tuple[Rule, ...] = Field(min_length=1, description="List of directives")
