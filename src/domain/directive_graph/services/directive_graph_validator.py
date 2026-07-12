"""DirectiveGraph validator — orchestrates all cross-directive specifications.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.services.evaluator_tree_validator import EvaluatorTreeValidator
from domain.directive_graph.services.lineage_validator import LineageValidator
from domain.directive_graph.specifications.audit_completeness import ActiveDirectiveRequiresAuthorSpec
from domain.directive_graph.specifications.evaluator_complexity import EvaluatorTreeComplexitySpec
from domain.directive_graph.specifications.metadata_size import MetadataSizeSpec
from domain.directive_graph.specifications.no_cycles import NoDeferToCyclesSpec
from domain.directive_graph.specifications.no_cycles import NoDependencyCyclesSpec
from domain.directive_graph.specifications.temporal_ordering import ExpiresAfterCreatedSpec
from domain.directive_graph.specifications.unique_ids import UniqueExecutionIdsSpec
from domain.directive_graph.specifications.unique_ids import UniqueLineageIdsSpec
from domain.directive_graph.specifications.valid_references import ValidCrossReferencesSpec


@dataclass(frozen=True)
class ValidationResult:
    """Structured result from graph-level validation.

    Attributes:
        is_valid (bool): True iff no errors were found.
        errors (tuple[str, ...]): Critical violations that must be resolved.
        warnings (tuple[str, ...]): Non-critical observations.
    """

    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


class DirectiveGraphValidator:
    """Orchestrates all cross-directive invariant checks.

    Runs every registered specification and domain service in order.
    Returns a structured ``ValidationResult`` — never raises for validation
    failures (only for programming errors in the caller).
    """

    def __init__(self) -> None:
        self._specs = [
            UniqueLineageIdsSpec(),
            UniqueExecutionIdsSpec(),
            ValidCrossReferencesSpec(),
            NoDependencyCyclesSpec(),
            NoDeferToCyclesSpec(),
            EvaluatorTreeComplexitySpec(),
            ActiveDirectiveRequiresAuthorSpec(),
            ExpiresAfterCreatedSpec(),
            MetadataSizeSpec(),
        ]
        self._evaluator_tree_validator = EvaluatorTreeValidator()
        self._lineage_validator = LineageValidator()

    def validate(self, graph: DirectiveGraph) -> ValidationResult:
        """Run all specifications and domain services against the graph.

        Args:
            graph (DirectiveGraph): The graph to validate.

        Returns:
            ValidationResult: Structured result with all errors collected.
        """
        errors: list[str] = []

        # Run all registered specifications
        for spec in self._specs:
            errors.extend(spec.violations(graph))

        # Run evaluator tree validator (separate domain service)
        for violation in self._evaluator_tree_validator.validate(graph):
            errors.append(f"[{violation.directive_id}] {violation.message}")

        # Run lineage validator
        for violation in self._lineage_validator.validate(graph):
            errors.append(f"[{violation.directive_id}] {violation.message}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=(),
        )
