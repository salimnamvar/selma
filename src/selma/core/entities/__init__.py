"""Core entities for Selma."""

from selma.core.entities.facts import DeclarationNode
from selma.core.entities.facts import FactDocument
from selma.core.entities.facts import LineNode
from selma.core.entities.facts import ParameterNode
from selma.core.entities.finding import Finding
from selma.core.entities.finding import Weight
from selma.core.entities.rule import EvaluatorConfig
from selma.core.entities.rule import Rule

__all__ = [
    "DeclarationNode",
    "EvaluatorConfig",
    "FactDocument",
    "Finding",
    "LineNode",
    "ParameterNode",
    "Rule",
    "Weight",
]
