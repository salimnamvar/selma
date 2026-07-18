"""Directive Graph bounded context.

Rich domain model for the rule_schema.json structural contract.
Wire-format translation lives in ``infrastructure.mappers.DirectiveGraphMapper``.
"""

from __future__ import annotations

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.factories.lifecycle import DirectiveLifecycleFactory
from domain.directive_graph.factories.lifecycle import LifecycleResult
from domain.directive_graph.repositories import DirectiveGraphRef
from domain.directive_graph.repositories import DirectiveGraphRepository
from domain.directive_graph.services.conflict_resolver import ConflictArtifact
from domain.directive_graph.services.conflict_resolver import ConflictResolutionResult
from domain.directive_graph.services.conflict_resolver import ConflictResolver
from domain.directive_graph.services.directive_graph_validator import DirectiveGraphValidator
from domain.directive_graph.services.directive_graph_validator import ValidationResult

__all__ = [
    "ConflictArtifact",
    "ConflictResolutionResult",
    "ConflictResolver",
    "Directive",
    "DirectiveGraph",
    "DirectiveGraphRef",
    "DirectiveGraphRepository",
    "DirectiveGraphValidator",
    "DirectiveLifecycleFactory",
    "LifecycleResult",
    "ValidationResult",
]
