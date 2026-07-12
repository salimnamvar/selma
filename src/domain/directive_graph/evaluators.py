"""Polymorphic evaluator hierarchy for the Directive Graph bounded context.

The evaluator hierarchy is a recursive discriminated union. Each evaluator
carries its own ``evaluator_type`` discriminator field (a ``Literal``), making
Pydantic's discriminated union machinery work without external routing.

JSON Schema format for sub-evaluators uses nested structure::

    {"evaluator_type": "regex", "evaluator_config": {"pattern": "...", "flags": ""}}

The ``_flatten_evaluator_entry`` ``BeforeValidator`` normalises this to the
flat domain form::

    {"evaluator_type": "regex", "pattern": "...", "flags": ""}

Top-level ``Directive`` evaluator fields are merged by a ``model_validator``
on ``Directive`` itself.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.4
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from domain.directive_graph.enums import (
    CompositeLogic,
    EvaluatorType,
    FieldCheckOperator,
    ThresholdOperator,
)
from domain.directive_graph.scalars import FiniteFloat, RegexFlags, RegexPattern


# ---------------------------------------------------------------------------
# BeforeValidator — normalises the sub-evaluator JSON Schema format
# ---------------------------------------------------------------------------


def _flatten_evaluator_entry(data: Any) -> Any:
    """Flatten ``{evaluator_type, evaluator_config: {...}}`` into a flat dict.

    Handles the JSON Schema representation for sub-evaluators inside composite
    evaluators.  If the data is already in the flat form (``evaluator_type``
    present, no nested ``evaluator_config``), it is returned unchanged.

    Args:
        data (Any): Raw input — expected to be a dict when normalisation applies.

    Returns:
        Any: Flattened dict suitable for discriminated union parsing, or the
            original value if no transformation is needed.
    """
    if not isinstance(data, dict):
        return data
    ev_type = data.get("evaluator_type")
    ev_config = data.get("evaluator_config")
    if ev_type is not None and isinstance(ev_config, dict) and "evaluator_type" not in ev_config:
        return {"evaluator_type": ev_type, **ev_config}
    return data


# ---------------------------------------------------------------------------
# Leaf evaluator value objects
# ---------------------------------------------------------------------------


class RegexEvaluator(BaseModel):
    """Evaluator that matches a field against a regular expression.

    Attributes:
        evaluator_type (Literal[EvaluatorType.REGEX]): Discriminator.
        pattern (RegexPattern): RE2-compatible regex pattern (length 1–4096).
        flags (RegexFlags): Regex modifier flags (combination of i, m, s).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.REGEX]
    pattern: RegexPattern
    flags: RegexFlags = ""


class FieldCheckEvaluator(BaseModel):
    """Evaluator that compares a target field against a static value.

    Attributes:
        evaluator_type (Literal[EvaluatorType.FIELD_CHECK]): Discriminator.
        field (str): Non-empty path within the target metadata or content.
        operator (FieldCheckOperator): Comparison operator.
        value (Any): Expected value to compare against.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.FIELD_CHECK]
    field: str = Field(min_length=1)
    operator: FieldCheckOperator
    value: Any


class ThresholdEvaluator(BaseModel):
    """Evaluator that tests a numeric field against a finite threshold.

    Attributes:
        evaluator_type (Literal[EvaluatorType.THRESHOLD]): Discriminator.
        field (str): Non-empty path within the target metadata or content.
        operator (ThresholdOperator): Numeric comparison operator.
        threshold (FiniteFloat): Finite IEEE 754 double threshold value.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.THRESHOLD]
    field: str = Field(min_length=1)
    operator: ThresholdOperator
    threshold: FiniteFloat


# ---------------------------------------------------------------------------
# Composite evaluator — recursive; uses forward reference
# ---------------------------------------------------------------------------


class CompositeEvaluator(BaseModel):
    """Boolean composition of sub-evaluators (AND, OR, NOT).

    Sub-evaluators are recursively typed as ``list["Evaluator"]``.
    ``CompositeEvaluator.model_rebuild()`` is called at the end of this
    module to resolve the forward reference.

    Invariants
    ----------
    - ``logic == NOT`` → exactly 1 sub-evaluator (schema ``maxItems: 1``).
    - ``len(sub_evaluators) >= 1`` (schema ``minItems: 1``).
    - ``len(sub_evaluators) <= 64`` (SPECIFICATION.md ``max_composite_width``).

    Attributes:
        evaluator_type (Literal[EvaluatorType.COMPOSITE]): Discriminator.
        logic (CompositeLogic): Boolean combinator.
        sub_evaluators (list[Evaluator]): Child evaluators (1–64 items).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.COMPOSITE]
    logic: CompositeLogic
    sub_evaluators: list["Evaluator"] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def _validate_not_cardinality(self) -> CompositeEvaluator:
        """Enforce that NOT logic has exactly 1 sub-evaluator.

        Raises:
            ValueError: If NOT logic has any count other than 1.
        """
        if self.logic == CompositeLogic.NOT and len(self.sub_evaluators) != 1:
            raise ValueError(
                f"CompositeEvaluator with NOT logic requires exactly 1 sub-evaluator; "
                f"got {len(self.sub_evaluators)}"
            )
        return self


# ---------------------------------------------------------------------------
# Discriminated union — the canonical Evaluator type
# ---------------------------------------------------------------------------

Evaluator = Annotated[
    Annotated[
        RegexEvaluator | FieldCheckEvaluator | ThresholdEvaluator | CompositeEvaluator,
        Field(discriminator="evaluator_type"),
    ],
    BeforeValidator(_flatten_evaluator_entry),
]
"""Discriminated union of all evaluator types.

The ``BeforeValidator`` handles the JSON Schema sub-evaluator format::

    {"evaluator_type": "regex", "evaluator_config": {"pattern": "..."}}

which is flattened to::

    {"evaluator_type": "regex", "pattern": "..."}

before discrimination.
"""

# MANDATORY: resolve the forward reference used in CompositeEvaluator.sub_evaluators.
CompositeEvaluator.model_rebuild()
