"""Tests for InspectionPipeline — pins, finding birth, capability gate."""

from __future__ import annotations

import pytest

from domain.authorization import CapabilityDeniedError, Role
from domain.finding import FsmState
from domain.inspection import ControlEvaluation, InspectionPipeline, InspectionStatus


@pytest.fixture
def pipeline() -> InspectionPipeline:
    return InspectionPipeline()


@pytest.mark.unit
@pytest.mark.domain
class TestInspectionPipeline:
    def test_submit_births_findings_for_fail(self, pipeline: InspectionPipeline) -> None:
        result = pipeline.submit(
            actor="cr-1",
            role=Role.COMPLIANCE_REPRESENTATIVE,
            target={"id": "t1", "payload": {"x": 1}},
            evaluations=[
                ControlEvaluation(
                    control_id="RULE-001",
                    lineage_id="RULE-001",
                    outcome="Fail",
                    severity="high",
                    evidence="broken",
                ),
                ControlEvaluation(
                    control_id="RULE-002",
                    lineage_id="RULE-002",
                    outcome="Pass",
                ),
            ],
            cg_ir_snapshot_hash="abc",
            frozen_env_hash="def",
            engine_version="8.2.4",
        )
        assert result.snapshot.status == InspectionStatus.COMPLETED
        assert len(result.findings) == 1
        assert result.findings[0].fsm_state == FsmState.OPEN
        assert result.snapshot.system_state_hash
        assert result.snapshot.target_hash

    def test_skipped_nodes_partial(self, pipeline: InspectionPipeline) -> None:
        result = pipeline.submit(
            actor="cr-1",
            role=Role.COMPLIANCE_REPRESENTATIVE,
            target={"id": "t1"},
            evaluations=[
                ControlEvaluation(
                    control_id="RULE-001",
                    lineage_id="RULE-001",
                    outcome="Fail",
                    skipped=True,
                ),
            ],
            cg_ir_snapshot_hash="abc",
            frozen_env_hash="def",
            engine_version="8.2.4",
        )
        assert result.snapshot.status == InspectionStatus.PARTIAL
        assert result.snapshot.skipped_nodes == ("RULE-001",)
        assert result.findings == ()

    def test_official_cannot_submit(self, pipeline: InspectionPipeline) -> None:
        with pytest.raises(CapabilityDeniedError):
            pipeline.submit(
                actor="ro-1",
                role=Role.REGULATORY_OFFICIAL,
                target={"id": "t1"},
                evaluations=[],
                cg_ir_snapshot_hash="abc",
                frozen_env_hash="def",
                engine_version="8.2.4",
            )

    def test_system_can_submit(self, pipeline: InspectionPipeline) -> None:
        result = pipeline.submit(
            actor="system",
            role=Role.SYSTEM,
            target={"id": "t1"},
            evaluations=[],
            cg_ir_snapshot_hash="abc",
            frozen_env_hash="def",
            engine_version="8.2.4",
        )
        assert result.snapshot.status == InspectionStatus.COMPLETED

    def test_reinspect_uses_reinspect_capability(self, pipeline: InspectionPipeline) -> None:
        # System lacks inspection.reinspect
        with pytest.raises(CapabilityDeniedError):
            pipeline.submit(
                actor="system",
                role=Role.SYSTEM,
                target={"id": "t1"},
                evaluations=[],
                cg_ir_snapshot_hash="abc",
                frozen_env_hash="def",
                engine_version="8.2.4",
                reinspect=True,
            )
        result = pipeline.submit(
            actor="cr-1",
            role=Role.COMPLIANCE_REPRESENTATIVE,
            target={"id": "t1"},
            evaluations=[],
            cg_ir_snapshot_hash="abc",
            frozen_env_hash="def",
            engine_version="8.2.4",
            reinspect=True,
        )
        assert result.snapshot.inspection_id
