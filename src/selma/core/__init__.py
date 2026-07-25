"""Core module for Selma."""

from selma.core.entities import DeclarationNode
from selma.core.entities import EvaluatorConfig
from selma.core.entities import FactDocument
from selma.core.entities import Finding
from selma.core.entities import LineNode
from selma.core.entities import ParameterNode
from selma.core.entities import Rule
from selma.core.entities import Weight
from selma.core.evaluators import CompositeEvaluator
from selma.core.evaluators import EvaluatorBase
from selma.core.evaluators import FieldCheckEvaluator
from selma.core.evaluators import RegexEvaluator
from selma.core.evaluators import ScriptEvaluator
from selma.core.evaluators import ThresholdEvaluator
from selma.core.ports import AbstractCache
from selma.core.ports import AbstractParser

__all__ = [
    "AbstractCache",
    "AbstractParser",
    "CompositeEvaluator",
    "DeclarationNode",
    "EvaluatorBase",
    "EvaluatorConfig",
    "FactDocument",
    "FieldCheckEvaluator",
    "Finding",
    "LineNode",
    "ParameterNode",
    "RegexEvaluator",
    "Rule",
    "ScriptEvaluator",
    "ThresholdEvaluator",
    "Weight",
]
