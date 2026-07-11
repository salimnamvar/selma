"""Domain enumerations — closed vocabularies from policy doctrine.

Conflict *algorithms* live in the compilation engine / SPECIFICATION.md.
This layer only holds declarative closed sets used by governance intent.
"""

from __future__ import annotations

from enum import StrEnum


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

    Ranks are explicit (1 = highest authority), not derived from declaration
    order, so reordering members cannot silently change governance semantics.
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"

    @property
    def rank(self) -> int:
        """Return 1-based authority rank (1 = highest)."""
        result: int
        match self:
            case PriorityCategory.CONSTITUTIONAL:
                result = 1
            case PriorityCategory.STATUTORY:
                result = 2
            case PriorityCategory.REGULATORY:
                result = 3
            case PriorityCategory.OPERATIONAL:
                result = 4
            case PriorityCategory.ADVISORY:
                result = 5
        return result


class ProhibitedField(StrEnum):
    """Machine-executable schema fields that must never appear in policy prose.

    Matches contamination_guard.prohibited_fields in policy_doctrine.yaml.
    """

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
