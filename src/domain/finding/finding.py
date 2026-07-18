"""Finding entity — aggregate root for the normative Finding FSM (§3.1)."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from domain.finding.enums import Disposition
from domain.finding.enums import FsmState
from domain.finding.enums import Severity


class Finding(BaseModel):
    """Regulatory finding with strict FSM state and disposition.

    Humans never close findings. Closure is system-automatic from
    ``Verified`` or ``Waived`` only.

    Attributes:
        finding_id: Stable UUID string for this finding instance.
        lineage_id: CG-IR node lineage root.
        control_id: Directive / CG-IR control identifier.
        inspection_id: Birth inspection instance.
        fsm_state: Current normative FSM state.
        disposition: valid | invalid | waived.
        severity: Severity classification.
        outcome: Evaluator outcome at birth.
        confidence: Evaluator confidence [0, 1].
        evidence: Evaluator evidence text.
        reasoning: Evaluator reasoning text.
        evidence_submitter: Actor who submitted remediation evidence (SoD-2).
        version: Optimistic concurrency projection version.
        actor: Last successful transition actor.
    """

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    lineage_id: str = Field(min_length=1)
    control_id: str = Field(min_length=1)
    inspection_id: str = Field(min_length=1)
    fsm_state: FsmState
    disposition: Disposition = Disposition.VALID
    severity: Severity
    outcome: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = ""
    reasoning: str = ""
    evidence_submitter: str | None = None
    version: int = Field(default=0, ge=0)
    actor: str = "system"

    @property
    def is_terminal(self) -> bool:
        """Return True if no further transitions are allowed."""
        return self.fsm_state in (FsmState.DISMISSED, FsmState.CLOSED)
