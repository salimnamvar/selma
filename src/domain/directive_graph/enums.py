"""Domain enumerations for the Directive Graph bounded context.

All enums inherit from StrEnum so values compare equal to their JSON string
representations (e.g. ``DeonticType.OBLIGATION == "obligation"`` is ``True``).

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.6
"""

from __future__ import annotations

from enum import StrEnum


class DeonticType(StrEnum):
    """Normative force of a directive: MUST, MUST NOT, MAY."""

    OBLIGATION = "obligation"
    PROHIBITION = "prohibition"
    PERMISSION = "permission"


class DirectiveStatus(StrEnum):
    """Lifecycle state of a directive."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class SeverityWeight(StrEnum):
    """Impact classification of a directive violation."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class PriorityLevel(StrEnum):
    """Hierarchical authority rank used in conflict resolution.

    Lower numeric value means higher authority.
    constitutional=1 (highest) … advisory=5 (lowest).
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


# Maps each PriorityLevel to its numeric rank (1 = highest authority).
PRIORITY_RANK: dict[PriorityLevel, int] = {
    PriorityLevel.CONSTITUTIONAL: 1,
    PriorityLevel.STATUTORY: 2,
    PriorityLevel.REGULATORY: 3,
    PriorityLevel.OPERATIONAL: 4,
    PriorityLevel.ADVISORY: 5,
}


class EvaluatorType(StrEnum):
    """Discriminator for the polymorphic evaluator hierarchy."""

    REGEX = "regex"
    FIELD_CHECK = "field_check"
    THRESHOLD = "threshold"
    COMPOSITE = "composite"


class CompositeLogic(StrEnum):
    """Boolean combinator for composite evaluators."""

    AND = "and"
    OR = "or"
    NOT = "not"


class FieldCheckOperator(StrEnum):
    """Comparison operators for field-check evaluators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    CONTAINS = "contains"
    MATCHES = "matches"


class ThresholdOperator(StrEnum):
    """Comparison operators for threshold evaluators."""

    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"


class FilterOperator(StrEnum):
    """Comparison operators for scope filters."""

    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    SUBSET = "subset"


class ConflictStrategy(StrEnum):
    """Explicit conflict override strategy."""

    ALWAYS_WINS = "always_wins"
    NEVER_WINS = "never_wins"
    DEFER_TO = "defer_to"


class LineageOperation(StrEnum):
    """Identity lifecycle operations that produce new execution IDs."""

    FORK = "fork"
    MERGE = "merge"
    SPLIT = "split"


class TargetType(StrEnum):
    """Kind of content a directive's scope applies to."""

    TEXT = "text"
    STRUCTURED = "structured"
    BINARY = "binary"
    ANY = "any"


class SemanticWeightType(StrEnum):
    """Relative importance of a non-surviving parent in a merge."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    INFORMATIONAL = "informational"


class LineagePreservation(StrEnum):
    """How lineage IDs are handled during dataset migration."""

    IDENTITY_PRESERVED = "identity_preserved"
    IDENTITY_REASSIGNED = "identity_reassigned"
    REQUIRES_REMAP = "requires_remap"
