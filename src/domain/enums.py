"""Domain Enumerations.

Enumerations for content types, identity operations, priority, and contamination.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum


class ContentType(StrEnum):
    """Content formats permitted in document sections."""

    PROSE = "prose"
    TABLE = "table"
    PROSE_OR_TABLE = "prose_or_table"
    MIXED = "mixed"


class IdentityOperation(StrEnum):
    """Lifecycle operations for rule lineage identity."""

    REVISION = "revision"
    FORK = "fork"
    MERGE = "merge"
    SPLIT = "split"
    RENAME = "rename"
    RETIRE = "retire"


class PriorityCategory(StrEnum):
    """Authority levels in the governance priority hierarchy.

    Declaration order matches ascending rank (1 = highest authority).
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"

    @property
    def rank(self) -> int:
        """Return 1-based authority rank from declaration order.

        Returns:
            int: Rank where 1 is highest authority.
        """
        result: int = list(type(self)).index(self) + 1
        return result


class ProhibitedField(StrEnum):
    """Schema fields that must never appear in policy prose."""

    PARAMETERS = "parameters"
    CONDITIONS = "conditions"
    EVALUATOR_HINT = "evaluator_hint"
    EVALUATOR_TYPE = "evaluator_type"
    EVALUATOR_CONFIG = "evaluator_config"
    WEIGHT = "weight"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    STATUS = "status"
    CREATED_AT = "created_at"
    EXPIRES_AT = "expires_at"
    REMEDIATION = "remediation"
    TARGET = "target"
    LINEAGE = "lineage"


class ResolutionStrategy(StrEnum):
    """Conflict resolution strategies in canonical precedence order."""

    EXPLICIT_OVERRIDE = "explicit_override"
    COMPATIBLE_OVERRIDES = "compatible_overrides"
    PRIORITY = "priority"
    SPECIFICITY = "specificity"
    RECENCY = "recency"
    CONFLICT_ARTIFACT = "conflict_artifact"


class PriorityRank(IntEnum):
    """Numeric authority ranks matching PriorityCategory declaration order."""

    CONSTITUTIONAL = 1
    STATUTORY = 2
    REGULATORY = 3
    OPERATIONAL = 4
    ADVISORY = 5
