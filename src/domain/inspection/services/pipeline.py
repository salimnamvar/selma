"""Inspection Execution Pipeline — six pure stages + finding birth.

Reference: docs/state-machine/selma_inspection_pipeline.puml, SPEC §2.10-§2.13

Design events include InspectionSubmitted, InspectionIngressGranted / Denied,
InspectionPinned, InspectionStagePassed / Fault, InspectionEvalRetried
(internal), InspectionAggregated, InspectionCompleted / Partial / Failed.
Stages are stable wait-points for completion events (doctrine process FSM).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import TYPE_CHECKING
from uuid import uuid4

from domain.authorization import AuthorizationService
from domain.authorization import Role
from domain.finding import Finding
from domain.finding import FindingLifecycle
from domain.finding import TransitionResult
from domain.finding.enums import EvaluatorOutcome
from domain.inspection.enums import InspectionStatus
from domain.inspection.models import ControlEvaluation
from domain.inspection.models import InspectionSnapshot

if TYPE_CHECKING:
    from domain.shared.events import DomainEvent


@dataclass(frozen=True)
class InspectionResult:
    """Outcome of a completed inspection pipeline instance."""

    snapshot: InspectionSnapshot
    findings: tuple[Finding, ...]
    events: tuple[DomainEvent, ...]


def _sha256_obj(a_obj: object) -> str:
    canonical = json.dumps(a_obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class InspectionPipeline:
    """Process FSM: one instance per inspection_id; reinspect = new instance."""

    def __init__(
        self,
        *,
        authz: AuthorizationService | None = None,
        findings: FindingLifecycle | None = None,
    ) -> None:
        self._authz = authz or AuthorizationService()
        self._findings = findings or FindingLifecycle(authz=self._authz)

    def submit(
        self,
        *,
        a_actor: str,
        a_role: Role,
        a_target: dict[str, object],
        a_evaluations: list[ControlEvaluation] | tuple[ControlEvaluation, ...],
        a_cg_ir_snapshot_hash: str,
        a_frozen_env_hash: str,
        a_engine_version: str,
        a_reinspect: bool = False,
        a_inspection_id: str | None = None,
    ) -> InspectionResult:
        """Run Submit → Ingress → six stages → Report → terminal status.

        ``evaluations`` are pure evaluator outputs (Evaluate stage). This
        domain service does not execute evaluators itself — it orchestrates
        pins, aggregation, finding birth, and immutability of the snapshot.
        """
        action = "inspection.reinspect" if a_reinspect else "inspection.submit"
        self._authz.enforce(a_actor=a_actor, a_role=a_role, a_action=action)

        iid = a_inspection_id or str(uuid4())
        # 1. Normalize
        target_hash = _sha256_obj(a_target)
        # Point-in-time pins (event stream excluded from system_state_hash)
        system_state_hash = _sha256_obj(
            {
                "cg_ir_snapshot_hash": a_cg_ir_snapshot_hash,
                "frozen_env_hash": a_frozen_env_hash,
                "engine_version": a_engine_version,
                "target_hash": target_hash,
            }
        )

        evals = tuple(a_evaluations)
        skipped = tuple(e.control_id for e in evals if e.skipped)

        finding_results: list[TransitionResult] = []
        for ev in evals:
            if ev.skipped:
                continue
            if ev.outcome not in {
                EvaluatorOutcome.FAIL.value,
                EvaluatorOutcome.PARTIAL.value,
                EvaluatorOutcome.NEEDS_REVIEW.value,
                "Fail",
                "Partial",
                "NeedsReview",
            }:
                continue
            finding_results.append(
                self._findings.create_from_inspection(
                    a_lineage_id=ev.lineage_id,
                    a_control_id=ev.control_id,
                    a_inspection_id=iid,
                    a_outcome=ev.outcome,
                    a_severity=ev.severity,
                    a_confidence=ev.confidence,
                    a_evidence=ev.evidence,
                    a_reasoning=ev.reasoning,
                )
            )

        if (skipped and finding_results) or (not finding_results and skipped):
            status = InspectionStatus.PARTIAL
        else:
            status = InspectionStatus.COMPLETED

        snapshot = InspectionSnapshot(
            inspection_id=iid,
            status=status,
            target_hash=target_hash,
            cg_ir_snapshot_hash=a_cg_ir_snapshot_hash,
            frozen_env_hash=a_frozen_env_hash,
            engine_version=a_engine_version,
            system_state_hash=system_state_hash,
            evaluations=evals,
            skipped_nodes=skipped,
            actor=a_actor,
        )
        findings = tuple(r.finding for r in finding_results)
        events: list[DomainEvent] = []
        for r in finding_results:
            events.extend(r.events)
        return InspectionResult(
            snapshot=snapshot,
            findings=findings,
            events=tuple(events),
        )
