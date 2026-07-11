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
    """Authority levels in the governance priority hierarchy."""

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"

    @property
    def rank(self) -> int:
        """Derive hierarchy rank from enum definition order (1 = highest)."""
        return list(PriorityCategory).index(self) + 1


class VersionComponent(StrEnum):
    """Components of a semantic version."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


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
