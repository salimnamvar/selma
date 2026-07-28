"""Domain enums — single source of truth for domain classifications.

All layers MUST import classifications from here. No duplicate StrEnums
for the same concept in infrastructure or interfaces.
"""

from __future__ import annotations

from enum import StrEnum


class DeonticType(StrEnum):
    """Deontic classification for rules (obligation / prohibition / permission).

    Used by: Rule, DirectivePolicy.
    """

    OBLIGATION = "obligation"
    PROHIBITION = "prohibition"
    PERMISSION = "permission"


class RuleStatus(StrEnum):
    """Lifecycle state of a rule.

    Used by: Rule.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class PriorityLevel(StrEnum):
    """Priority level for conflict resolution.

    Used by: Rule, PriorityHierarchy.
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


class Severity(StrEnum):
    """Severity level for findings and rule weight.

    Used by: Finding, Rule.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class PureEvaluatorType(StrEnum):
    """Language-agnostic evaluator types from rule_schema.json.

    Language-specific engines (e.g. ast_walk) use free-form strings on Rule
    and are not members of this pure set.
    """

    REGEX = "regex"
    FIELD_CHECK = "field_check"
    THRESHOLD = "threshold"
    COMPOSITE = "composite"


class ComparisonOperator(StrEnum):
    """Comparison operators for field_check evaluators."""

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


class ContentType(StrEnum):
    """Content type for policy document sections."""

    PROSE = "prose"
    TABLE = "table"
    PROSE_OR_TABLE = "prose_or_table"
    MIXED = "mixed"


class PriorityCategory(StrEnum):
    """Priority hierarchy categories in policy doctrine."""

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"
