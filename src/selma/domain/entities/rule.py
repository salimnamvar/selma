"""Rule aggregate root — the core domain entity for lint rules.

Has identity (RuleId), carries behavior, enforces invariants.
Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from selma.domain.value_objects.guidance import RuleGuidance
from selma.domain.value_objects.severity import Severity


class EvaluatorConfig(BaseModel):
    """Configuration for a rule evaluator."""

    model_config = ConfigDict(frozen=True)

    pattern: str | None = None
    flags: str | None = None
    target_field: str | None = None
    operator: str | None = None
    value: str | int | float | bool | None = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: tuple[EvaluatorConfig, ...] = ()
    target_node: str | None = None
    walk_nodes: tuple[str, ...] = ()
    conditions: tuple[dict[str, object], ...] = ()
    forbidden_calls: tuple[dict[str, str], ...] = ()
    forbidden_functions: tuple[str, ...] = ()
    exempt_module_methods: tuple[str, ...] = ()
    resource_calls: tuple[str, ...] = ()
    execute_methods: tuple[str, ...] = ()
    sql_keywords: tuple[str, ...] = ()
    io_calls: tuple[str, ...] = ()
    check_first_arg: dict[str, bool] = Field(default_factory=dict)
    count: dict[str, object] = Field(default_factory=dict)
    message_template: str = ""
    exempt_dunders: bool = True
    exempt_generators: bool = True
    exempt_names: tuple[str, ...] = ()
    max_lines: int = 60


class RuleDefinition(BaseModel):
    """Rule definition loaded from JSON. Immutable.

    This is the domain representation of a rule.
    """

    model_config = ConfigDict(frozen=True)

    lineage_id: str
    id: str
    rule_type: str  # obligation, prohibition, permission
    message: str
    evaluator_type: str
    evaluator_config: EvaluatorConfig
    weight: Severity = Severity.MEDIUM
    priority: str = "operational"
    status: str = "active"
    created_at: str = ""
    rationale: str = ""
    remediation: str = ""
    guidance: RuleGuidance | None = None
    parameters: dict[str, object] = Field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()

    @property
    def rule_id(self) -> str:
        return self.lineage_id

    def is_active(self) -> bool:
        return self.status == "active"
