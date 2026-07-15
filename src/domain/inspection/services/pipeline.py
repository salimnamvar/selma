"""Inspection Execution Pipeline — six pure stages + finding birth.

Reference: docs/state-machine/selma_inspection_pipeline.puml, SPEC §2.10–§2.13
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from uuid import uuid4

from domain.authorization import AuthorizationService, Role
from domain.finding import Finding, FindingLifecycle, TransitionResult
from domain.finding.enums import EvaluatorOutcome
from domain.inspection.enums import InspectionStatus
from domain.inspection.models import ControlEvaluation, InspectionSnapshot
from domain.shared.events import DomainEvent


@dataclass(frozen=True)
class InspectionResult:
    """Outcome of a completed inspection pipeline instance."""

    snapshot: InspectionSnapshot
    findings: tuple[Finding, ...]
    events: tuple[DomainEvent, ...]


def _sha256_obj(obj: object) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
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
        actor: str,
        role: Role,
        target: dict[str, object],
        evaluations: list[ControlEvaluation] | tuple[ControlEvaluation, ...],
        cg_ir_snapshot_hash: str,
        frozen_env_hash: str,
        engine_version: str,
        reinspect: bool = False,
        inspection_id: str | None = None,
    ) -> InspectionResult:
        """Run Submit → Ingress → six stages → Report → terminal status.

        ``evaluations`` are pure evaluator outputs (Evaluate stage). This
        domain service does not execute evaluators itself — it orchestrates
        pins, aggregation, finding birth, and immutability of the snapshot.
        """
        action = "inspection.reinspect" if reinspect else "inspection.submit"
        self._authz.enforce(actor=actor, role=role, action=action)

        iid = inspection_id or str(uuid4())
        # 1. Normalize
        target_hash = _sha256_obj(target)
        # Point-in-time pins (event stream excluded from system_state_hash)
        system_state_hash = _sha256_obj(
            {
                "cg_ir_snapshot_hash": cg_ir_snapshot_hash,
                "frozen_env_hash": frozen_env_hash,
                "engine_version": engine_version,
                "target_hash": target_hash,
            }
        )

        evals = tuple(evaluations)
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
                    lineage_id=ev.lineage_id,
                    control_id=ev.control_id,
                    inspection_id=iid,
                    outcome=ev.outcome,
                    severity=ev.severity,
                    confidence=ev.confidence,
                    evidence=ev.evidence,
                    reasoning=ev.reasoning,
                )
            )

        if skipped and finding_results:
            status = InspectionStatus.PARTIAL
        elif not finding_results and skipped:
            status = InspectionStatus.PARTIAL
        else:
            status = InspectionStatus.COMPLETED

        snapshot = InspectionSnapshot(
            inspection_id=iid,
            status=status,
            target_hash=target_hash,
            cg_ir_snapshot_hash=cg_ir_snapshot_hash,
            frozen_env_hash=frozen_env_hash,
            engine_version=engine_version,
            system_state_hash=system_state_hash,
            evaluations=evals,
            skipped_nodes=skipped,
            actor=actor,
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
