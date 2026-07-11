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

    Numeric ranks live on ``PriorityLevel.rank`` in YAML — not on the enum.
    """

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


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
