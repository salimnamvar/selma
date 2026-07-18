"""Graph-level specifications (business invariants)."""

from __future__ import annotations

from domain.directive_graph.specifications.base import Specification
from domain.directive_graph.specifications.evaluator_complexity import EvaluatorTreeComplexitySpec
from domain.directive_graph.specifications.metadata_size import MetadataSizeSpec
from domain.directive_graph.specifications.no_cycles import NoDeferToCyclesSpec
from domain.directive_graph.specifications.no_cycles import NoDependencyCyclesSpec
from domain.directive_graph.specifications.supersession import SupersessionBindingSpec
from domain.directive_graph.specifications.unique_ids import UniqueExecutionIdsSpec
from domain.directive_graph.specifications.valid_references import ValidCrossReferencesSpec

__all__ = [
    "EvaluatorTreeComplexitySpec",
    "MetadataSizeSpec",
    "NoDeferToCyclesSpec",
    "NoDependencyCyclesSpec",
    "Specification",
    "SupersessionBindingSpec",
    "UniqueExecutionIdsSpec",
    "ValidCrossReferencesSpec",
]
