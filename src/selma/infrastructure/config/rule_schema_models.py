"""Pydantic v2 models for rule JSON documents.

Mirrors schema/rule_schema.json for typed access after jsonschema validation.
The engine never hardcodes rule identities; it only consumes these structures.
"""

from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from selma.domain.value_objects.severity import Severity


class RuleGuidanceModel(BaseModel):
    """Optional guidance block attached to a rule document."""

    model_config = ConfigDict(extra="allow")

    correct_example: str | None = None
    incorrect_example: str | None = None
    explanation: str | None = None
    severity: str | None = None


class ConditionModel(BaseModel):
    """Declarative AST condition node (supports all_of / any_of / not)."""

    model_config = ConfigDict(extra="allow")

    field: str | None = None
    operator: str | None = None
    value: Any = None
    all_of: list[ConditionModel] | None = None
    any_of: list[ConditionModel] | None = None
    not_cond: ConditionModel | None = Field(default=None, alias="not")


class EvaluatorConfigModel(BaseModel):
    """Evaluator configuration payload for a rule document."""

    model_config = ConfigDict(extra="allow")

    pattern: str | None = None
    flags: str | None = None
    field: str | None = None
    operator: str | None = None
    value: Any = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: list[Any] = Field(default_factory=list)
    target_node: str | None = None
    root_node: str | None = None
    walk_nodes: list[str] = Field(default_factory=list)
    walk_config: dict[str, Any] = Field(default_factory=dict)
    conditions: list[Any] = Field(default_factory=list)
    forbidden_calls: list[Any] = Field(default_factory=list)
    forbidden_functions: list[str] = Field(default_factory=list)
    resource_calls: list[str] = Field(default_factory=list)
    execute_methods: list[str] = Field(default_factory=list)
    sql_keywords: list[str] = Field(default_factory=list)
    io_calls: list[str] = Field(default_factory=list)
    check_first_arg: dict[str, bool] = Field(default_factory=dict)
    count: dict[str, Any] = Field(default_factory=dict)
    message_template: str = ""
    exempt_dunders: bool = True
    exempt_generators: bool = True
    exempt_names: list[str] = Field(default_factory=list)
    max_lines: int = 60
    check: dict[str, Any] = Field(default_factory=dict)
    target_methods: list[str] = Field(default_factory=list)
    exempt_if: dict[str, Any] = Field(default_factory=dict)


class RuleDocumentModel(BaseModel):
    """Single rule JSON document validated against rule_schema.json."""

    model_config = ConfigDict(extra="allow")

    lineage_id: str
    id: str
    type: Literal["obligation", "prohibition", "permission"]
    message: str
    evaluator_type: str
    evaluator_config: EvaluatorConfigModel
    status: str = "active"
    created_at: str = ""
    weight: str | Severity = "medium"
    priority: str = "operational"
    rationale: str = ""
    remediation: str = ""
    guidance: RuleGuidanceModel | dict[str, Any] | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)
