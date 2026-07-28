"""Rule aggregate root — the core domain entity for lint rules.

Has identity (lineage_id), carries behavior, enforces invariants.
Uses Pydantic v2 BaseModel with frozen config.

Language-agnostic. The evaluator_type and evaluator_config define
what this rule checks. Language-specific extensions are handled by
the infrastructure layer.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity


class EvaluatorConfig(BaseModel):
    """Configuration for a rule evaluator.

    Language-agnostic flexible container. Accepts any evaluator
    configuration fields via extra="allow". Language-specific fields
    (e.g. walk_nodes for Python AST) are passed through as extras.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    # Pure evaluator fields (language-agnostic core)
    pattern: str | None = None
    flags: str | None = None
    field: str | None = None
    operator: str | None = None
    value: str | int | float | bool | None = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: tuple[EvaluatorConfig, ...] = ()


class RuleDefinition(BaseModel):
    """Rule definition loaded from JSON. Immutable.

    This is the domain representation of a rule.
    Language-agnostic — language-specific behavior is in evaluator_config extras.
    """

    model_config = ConfigDict(frozen=True)

    lineage_id: str
    id: str
    rule_type: DeonticType
    message: str
    evaluator_type: str
    evaluator_config: EvaluatorConfig
    weight: Severity = Severity.MEDIUM
    priority: PriorityLevel = PriorityLevel.OPERATIONAL
    status: RuleStatus = RuleStatus.ACTIVE
    created_at: str = ""
    rationale: str = ""
    remediation: str = ""
    guidance: dict[str, Any] | None = None
    parameters: dict[str, object] = Field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    anchor_ref: str = ""
    scope: dict[str, Any] | None = None
    conflict_resolution: dict[str, Any] | None = None

    @property
    def rule_id(self) -> str:
        """Get the lineage ID (immutable root)."""
        return self.lineage_id

    def is_active(self) -> bool:
        """Check if this rule is active."""
        return self.status == RuleStatus.ACTIVE
