"""Rule aggregate root — the core domain entity for lint rules.

Has identity (RuleId), carries behavior, enforces invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.guidance import RuleGuidance
from selma.domain.value_objects.rule_id import RuleId
from selma.domain.value_objects.severity import Severity


@dataclass(frozen=True)
class EvaluatorConfig:
    """Configuration for a rule evaluator."""

    pattern: str | None = None
    flags: str | None = None
    field: str | None = None
    operator: str | None = None
    value: str | int | float | bool | None = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: tuple[EvaluatorConfig, ...] = ()
    target_node: str | None = None
    walk_nodes: tuple[str, ...] = ()
    forbidden_calls: tuple[dict[str, str], ...] = ()
    forbidden_functions: tuple[str, ...] = ()
    resource_calls: tuple[str, ...] = ()
    execute_methods: tuple[str, ...] = ()
    sql_keywords: tuple[str, ...] = ()
    io_calls: tuple[str, ...] = ()
    check_first_arg: dict[str, bool] = field(default_factory=dict)
    count: dict[str, object] = field(default_factory=dict)
    message_template: str = ""
    exempt_dunders: bool = True
    exempt_generators: bool = True
    exempt_names: tuple[str, ...] = ()
    max_lines: int = 60


@dataclass(frozen=True)
class RuleDefinition:
    """Rule definition loaded from JSON. Immutable.

    This is the domain representation of a rule. It does NOT depend on
    any infrastructure (no Pydantic, no JSON parsing).
    """

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
    parameters: dict[str, object] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()

    @property
    def rule_id(self) -> RuleId:
        return RuleId(self.lineage_id)

    def is_active(self) -> bool:
        return self.status == "active"
