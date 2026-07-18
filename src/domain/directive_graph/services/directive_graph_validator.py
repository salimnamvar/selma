"""DirectiveGraph validator — orchestrates all cross-directive specifications.

Entity-local invariants (active author, expires_at ordering, NOT cardinality)
are enforced at construction time. This service only runs multi-object rules.

Reference: SPECIFICATION.md §2.2.3, §2.9, §2.15
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from domain.directive_graph.services.lineage_validator import LineageValidator
from domain.directive_graph.specifications.evaluator_complexity import EvaluatorTreeComplexitySpec
from domain.directive_graph.specifications.metadata_size import MetadataSizeSpec
from domain.directive_graph.specifications.no_cycles import NoDeferToCyclesSpec
from domain.directive_graph.specifications.no_cycles import NoDependencyCyclesSpec
from domain.directive_graph.specifications.supersession import SupersessionBindingSpec
from domain.directive_graph.specifications.unique_ids import UniqueExecutionIdsSpec
from domain.directive_graph.specifications.valid_references import ValidCrossReferencesSpec

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph
    from domain.directive_graph.specifications.base import Specification


@dataclass(frozen=True)
class ValidationResult:
    """Structured result from graph-level validation.

    Attributes:
        is_valid: True iff no errors were found.
        errors: Critical violations that must be resolved.
        warnings: Non-critical observations.
    """

    is_valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


class DirectiveGraphValidator:
    """Orchestrates all cross-directive invariant checks.

    Runs every registered specification and the lineage domain service.
    Returns a structured ``ValidationResult`` — never raises for validation
    failures (only for programming errors in the caller).
    """

    def __init__(self) -> None:
        """Register default specifications and the lineage validator."""
        self._specs: list[Specification[DirectiveGraph]] = [
            UniqueExecutionIdsSpec(),
            ValidCrossReferencesSpec(),
            NoDependencyCyclesSpec(),
            NoDeferToCyclesSpec(),
            EvaluatorTreeComplexitySpec(),
            MetadataSizeSpec(),
            SupersessionBindingSpec(),
        ]
        self._lineage_validator = LineageValidator()

    def validate(self, a_graph: DirectiveGraph) -> ValidationResult:
        """Run all specifications and domain services against the graph.

        Args:
            a_graph: The graph to validate.

        Returns:
            Structured result with all errors collected.
        """
        errors: list[str] = []

        for spec in self._specs:
            errors.extend(spec.violations(a_graph))

        for violation in self._lineage_validator.validate(a_graph):
            errors.append(f"[{violation.directive_id}] {violation.message}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=(),
        )
