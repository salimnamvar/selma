"""Rule input model for Selma."""

from pydantic import BaseModel


class EvaluatorConfig(BaseModel):
    """Configuration for an evaluator."""

    pattern: str | None = None
    flags: str | None = None
    field: str | None = None
    operator: str | None = None
    value: str | int | float | bool | None = None
    threshold: float | None = None
    logic: str | None = None
    sub_evaluators: list["EvaluatorConfig"] | None = None


class Rule(BaseModel):
    """A lint rule loaded from JSON."""

    id: str
    message: str
    evaluator_type: str
    evaluator_config: EvaluatorConfig
    weight: str = "medium"
    metadata: dict = {}
