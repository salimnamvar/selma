"""Domain enums — single source of truth for domain classifications.

These enums are used across domain entities, infrastructure models,
and schema validation. All other modules MUST import from here.
"""

from __future__ import annotations

from enum import StrEnum


class DeonticType(StrEnum):
    """Deontic classification for rules.

    Obligation (MUST), Prohibition (MUST NOT), Permission (MAY).
    Used by: RuleDefinition, Rule schema model, DirectivePolicy.
    """

    OBLIGATION = "obligation"
    PROHIBITION = "prohibition"
    PERMISSION = "permission"


class RuleStatus(StrEnum):
    """Lifecycle state of a rule.

    Used by: RuleDefinition, Rule schema model.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


class PriorityLevel(StrEnum):
    """Priority level for conflict resolution.

    Used by: RuleDefinition, Rule schema model, PriorityHierarchy.
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


class Severity(StrEnum):
    """Severity level for findings.

    Used by: Finding, RuleDefinition, Rule schema model.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"
