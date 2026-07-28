"""Rule entity and machine-executable rule graph models.

Single source of truth for the structural projection of rule_schema.json.
Language-specific evaluator types (e.g. ast_walk) are free-form strings;
pure types are documented in PureEvaluatorType.

Infrastructure MUST import these types — never redefine them.
"""

from __future__ import annotations

from typing import Annotated
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from selma.domain.value_objects.enums import ComparisonOperator
from selma.domain.value_objects.enums import ConflictStrategy
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import FilterOperator
from selma.domain.value_objects.enums import LineageOperation
from selma.domain.value_objects.enums import LineagePreservation
from selma.domain.value_objects.enums import LogicOp
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import PureEvaluatorType
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.enums import TargetType
from selma.domain.value_objects.enums import ThresholdOperator

# ─── Evaluator configs (pure types + flexible engine config) ─────────────────


class RegexEvaluatorConfig(BaseModel):
    """Regex evaluator config — matches text patterns."""

    model_config = ConfigDict(frozen=True)

    pattern: str = Field(min_length=1, max_length=4096)
    flags: str = Field(default="", pattern="^[ims]*$")


class FieldCheckEvaluatorConfig(BaseModel):
    """Field check evaluator config — compares field values."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(min_length=1)
    operator: ComparisonOperator
    value: Any


class ThresholdEvaluatorConfig(BaseModel):
    """Threshold evaluator config — numeric comparisons."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(min_length=1)
    operator: ThresholdOperator
    threshold: float


class CompositeEvaluatorConfig(BaseModel):
    """Composite evaluator config — logical combinations."""

    model_config = ConfigDict(frozen=True)

    logic: LogicOp
    sub_evaluators: tuple[EvaluatorConfigEntry, ...] = Field(
        min_length=1,
        max_length=64,
    )


class EvaluatorConfigEntry(BaseModel):
    """Tagged sub-evaluator entry within a composite evaluator."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: PureEvaluatorType
    evaluator_config: (
        RegexEvaluatorConfig
        | FieldCheckEvaluatorConfig
        | ThresholdEvaluatorConfig
        | CompositeEvaluatorConfig
    )


CompositeEvaluatorConfig.model_rebuild()


class RegexEvaluator(BaseModel):
    """Regex evaluator — matches text patterns."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[PureEvaluatorType.REGEX] = PureEvaluatorType.REGEX
    evaluator_config: RegexEvaluatorConfig


class FieldCheckEvaluator(BaseModel):
    """Field check evaluator — compares field values."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[PureEvaluatorType.FIELD_CHECK] = (
        PureEvaluatorType.FIELD_CHECK
    )
    evaluator_config: FieldCheckEvaluatorConfig


class ThresholdEvaluator(BaseModel):
    """Threshold evaluator — numeric comparisons."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[PureEvaluatorType.THRESHOLD] = PureEvaluatorType.THRESHOLD
    evaluator_config: ThresholdEvaluatorConfig


class CompositeEvaluator(BaseModel):
    """Composite evaluator — logical combinations."""

    model_config = ConfigDict(frozen=True)

    evaluator_type: Literal[PureEvaluatorType.COMPOSITE] = PureEvaluatorType.COMPOSITE
    evaluator_config: CompositeEvaluatorConfig


TypedEvaluator = Annotated[
    RegexEvaluator | FieldCheckEvaluator | ThresholdEvaluator | CompositeEvaluator,
    Field(discriminator="evaluator_type"),
]


class EvaluatorConfig(BaseModel):
    """Flexible evaluator configuration for pure and language-specific engines.

    Core pure fields are optional; language extensions pass through via extra.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    pattern: str | None = None
    flags: str | None = None
    field: str | None = None
    operator: str | None = None
    value: str | int | float | bool | None = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: tuple[EvaluatorConfig, ...] = ()


# ─── Scope ───────────────────────────────────────────────────────────────────


class ScopeFilter(BaseModel):
    """A single applicability filter predicate."""

    model_config = ConfigDict(frozen=True)

    field: str
    operator: FilterOperator
    value: Any


class Scope(BaseModel):
    """Structured applicability context."""

    model_config = ConfigDict(frozen=True)

    target_type: TargetType = TargetType.ANY
    domain: str = ""
    jurisdiction: str = ""
    filters: tuple[ScopeFilter, ...] = ()


# ─── Metadata / lineage / conflict ───────────────────────────────────────────


class AuditMetadata(BaseModel):
    """Audit metadata for a rule."""

    model_config = ConfigDict(frozen=True)

    authored_by: str = ""
    approved_by: str = ""
    approved_at: str = ""


class RuleMetadata(BaseModel):
    """Per-rule metadata. Informational only."""

    model_config = ConfigDict(frozen=True, extra="allow")

    audit: AuditMetadata = Field(default_factory=AuditMetadata)


class ConflictResolution(BaseModel):
    """Explicit conflict resolution override."""

    model_config = ConfigDict(frozen=True)

    strategy: ConflictStrategy
    defer_to: str | None = None

    @field_validator("defer_to")
    @classmethod
    def validate_defer_to(cls, v: str | None, info: Any) -> str | None:
        """Require defer_to when strategy is defer_to (Pydantic contract)."""
        b_continue = True
        result = v
        needs_defer = info.data.get("strategy") == ConflictStrategy.DEFER_TO
        if b_continue and needs_defer and not v:
            b_continue = False
            msg = "defer_to is required when strategy is defer_to"
            raise ValueError(msg)
        if b_continue:
            result = v
        return result


class Lineage(BaseModel):
    """Tracks identity lifecycle operations."""

    model_config = ConfigDict(frozen=True)

    operation: LineageOperation
    parent_lineage_ids: tuple[str, ...] = Field(min_length=1)
    parent_execution_ids: tuple[str, ...] = Field(min_length=1)
    timestamp: str
    reason: str = ""


# ─── Rule entity ─────────────────────────────────────────────────────────────


class Rule(BaseModel):
    """Machine-executable rule — domain entity and document model.

    Paired with DirectivePolicy inside a Directive aggregate.
    """

    model_config = ConfigDict(frozen=True)

    lineage_id: str = Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+[A-Z]?$",
        description="Immutable root identifier",
    )
    id: str = Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+[A-Z]?(-[A-Z0-9]+)*$",
        description="Active execution identifier",
    )
    type: DeonticType
    message: str = Field(min_length=1)
    evaluator_type: str = Field(
        min_length=1,
        description="Pure type or language-specific engine name",
    )
    evaluator_config: EvaluatorConfig = Field(
        default_factory=EvaluatorConfig,
        description="Evaluator configuration (extra fields allowed)",
    )
    status: RuleStatus = RuleStatus.ACTIVE
    created_at: str = ""
    target: str = ""
    scope: Scope | None = None
    anchor_ref: str = ""
    directive_revision: str = ""
    control_version: str = ""
    metadata: RuleMetadata = Field(default_factory=RuleMetadata)
    weight: Severity = Severity.MEDIUM
    priority: PriorityLevel = PriorityLevel.OPERATIONAL
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    conflict_resolution: ConflictResolution | None = None
    expires_at: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    remediation: str = ""
    lineage: Lineage | None = None

    @property
    def rule_id(self) -> str:
        """Immutable lineage root."""
        return self.lineage_id

    def is_active(self) -> bool:
        """Whether this rule participates in inspection."""
        return self.status == RuleStatus.ACTIVE

    def is_pure_evaluator(self) -> bool:
        """Whether evaluator_type is a pure schema type."""
        return self.evaluator_type in {member.value for member in PureEvaluatorType}


# ─── Dataset-level models ────────────────────────────────────────────────────


class MergeProvenanceParent(BaseModel):
    """Non-surviving parent in a merge operation."""

    model_config = ConfigDict(frozen=True)

    lineage_id: str
    semantic_weight: str = "informational"
    context: str = ""


class MergeProvenance(BaseModel):
    """Merge provenance tracking."""

    model_config = ConfigDict(frozen=True)

    non_surviving_parents: tuple[MergeProvenanceParent, ...] = Field(min_length=1)
    merged_at: str = ""
    merge_notes: str = ""


class MigrationMetadata(BaseModel):
    """Migration metadata for a rule dataset."""

    model_config = ConfigDict(frozen=True)

    superseded_by: str = ""
    migration_notes: str = ""
    upgrade_from: str = ""
    upgrade_to: str = ""
    migration_required: bool = False
    lineage_preservation: LineagePreservation | None = None
    merge_provenance: MergeProvenance | None = None


class DatasetAuditMetadata(BaseModel):
    """Dataset-level audit metadata."""

    model_config = ConfigDict(frozen=True)

    authored_by: str = ""
    approved_by: str = ""
    approved_at: str = ""


class DatasetMetadata(BaseModel):
    """Dataset-level metadata. Informational only."""

    model_config = ConfigDict(frozen=True, extra="allow")

    audit: DatasetAuditMetadata = Field(default_factory=DatasetAuditMetadata)
    vendor: dict[str, str] = Field(default_factory=dict)
    author: dict[str, str] = Field(default_factory=dict)
    migration: MigrationMetadata | None = None
    domain: str = ""
    jurisdiction: str = ""
    project: str = ""


class RuleDataset(BaseModel):
    """Wrapped rule dataset document (machine-executable governance layer)."""

    model_config = ConfigDict(frozen=True)

    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    policy_contract_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    policy_contract_id: str = "universal-policy-doctrine"
    metadata: DatasetMetadata = Field(default_factory=DatasetMetadata)
    rules: tuple[Rule, ...] = Field(min_length=1)
