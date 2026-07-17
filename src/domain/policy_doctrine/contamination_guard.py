"""Contamination guard — fields prohibited in policy-layer prose."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ProhibitedField(StrEnum):
    """Machine-executable schema fields that must never appear in policy prose."""

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


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: frozenset[ProhibitedField] = Field(
        min_length=14, description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[str, ...] = Field(
        min_length=1, description="How Machine IDs may appear in policy"
    )
    metadata_constraints: str = Field(min_length=1, description="Constraints on schema metadata in policy")
