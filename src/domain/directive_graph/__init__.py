"""Directive Graph bounded context.

Rich domain model for the rule_schema.json structural contract.
Wire-format translation lives in ``infrastructure.mappers.DirectiveGraphMapper``.
"""

from __future__ import annotations

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.factories.lifecycle import DirectiveLifecycleFactory, LifecycleResult
from domain.directive_graph.repositories import DirectiveGraphRef, DirectiveGraphRepository
from domain.directive_graph.services.conflict_resolver import (
    ConflictArtifact,
    ConflictResolutionResult,
    ConflictResolver,
)
from domain.directive_graph.services.directive_graph_validator import DirectiveGraphValidator, ValidationResult

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
