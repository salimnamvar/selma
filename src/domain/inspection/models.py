"""Inspection run snapshot value objects."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.inspection.enums import InspectionStatus


class ControlEvaluation(BaseModel):
    """Per-control pure evaluation result before finding birth."""

    model_config = ConfigDict(extra="forbid")

    control_id: str
    lineage_id: str
    outcome: str  # Pass | Fail | Partial | NeedsReview
    severity: str = "medium"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str = ""
    reasoning: str = ""
    skipped: bool = False


class InspectionSnapshot(BaseModel):
    """Immutable point-in-time inspection result (§2.13)."""

    model_config = ConfigDict(extra="forbid")

    inspection_id: str
    status: InspectionStatus
    target_hash: str
    cg_ir_snapshot_hash: str
    frozen_env_hash: str
    engine_version: str
    system_state_hash: str
    evaluations: tuple[ControlEvaluation, ...] = ()
    skipped_nodes: tuple[str, ...] = ()
    actor: str
