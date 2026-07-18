"""Polymorphic evaluator hierarchy for the Directive Graph bounded context.

The evaluator hierarchy is a recursive discriminated union. Each evaluator
carries its own ``evaluator_type`` discriminator field (a ``Literal``).

Domain shape is flat::

    {"evaluator_type": "regex", "pattern": "...", "flags": ""}

Wire/schema nested form is normalised by the anti-corruption layer, not here.

Reference: SPECIFICATION.md §2.9
"""

from __future__ import annotations

from typing import Annotated
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from domain.directive_graph.enums import CompositeLogic
from domain.directive_graph.enums import EvaluatorType
from domain.directive_graph.enums import FieldCheckOperator
from domain.directive_graph.enums import ThresholdOperator
from domain.directive_graph.scalars import FiniteFloat
from domain.directive_graph.scalars import RegexFlags
from domain.directive_graph.scalars import RegexPattern

# ---------------------------------------------------------------------------
# Leaf evaluator value objects
# ---------------------------------------------------------------------------


class RegexEvaluator(BaseModel):
    """Evaluator that matches a field against a regular expression.

    Attributes:
        evaluator_type: Discriminator.
        pattern: RE2-compatible regex pattern (length 1-4096).
        flags: Regex modifier flags (combination of i, m, s).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.REGEX]
    pattern: RegexPattern
    flags: RegexFlags = ""


class FieldCheckEvaluator(BaseModel):
    """Evaluator that compares a target field against a static value.

    Attributes:
        evaluator_type: Discriminator.
        field: Non-empty path within the target metadata or content.
        operator: Comparison operator.
        value: Expected value to compare against.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.FIELD_CHECK]
    field: str = Field(min_length=1)
    operator: FieldCheckOperator
    value: Any


class ThresholdEvaluator(BaseModel):
    """Evaluator that tests a numeric field against a finite threshold.

    Attributes:
        evaluator_type: Discriminator.
        field: Non-empty path within the target metadata or content.
        operator: Numeric comparison operator.
        threshold: Finite IEEE 754 double threshold value.
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
        evaluator_type: Discriminator.
        logic: Boolean combinator.
        sub_evaluators: Child evaluators (1-64 items).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evaluator_type: Literal[EvaluatorType.COMPOSITE]
    logic: CompositeLogic
    sub_evaluators: list[Evaluator] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def _validate_not_cardinality(self) -> CompositeEvaluator:
        """Enforce that NOT logic has exactly 1 sub-evaluator.

        Raises:
            ValueError: If NOT logic has any count other than 1.
        """
        if self.logic == CompositeLogic.NOT and len(self.sub_evaluators) != 1:
            msg = f"CompositeEvaluator with NOT logic requires exactly 1 sub-evaluator; got {len(self.sub_evaluators)}"
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Discriminated union — the canonical Evaluator type
# ---------------------------------------------------------------------------

Evaluator = Annotated[
    RegexEvaluator | FieldCheckEvaluator | ThresholdEvaluator | CompositeEvaluator,
    Field(discriminator="evaluator_type"),
]
"""Discriminated union of all evaluator types (domain-shaped, flat)."""

# MANDATORY: resolve the forward reference used in CompositeEvaluator.sub_evaluators.
CompositeEvaluator.model_rebuild()
