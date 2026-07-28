"""Domain aggregates — consistency boundaries."""

from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.aggregates.lint_result import LintResult

__all__ = [
    "Directive",
    "DirectiveCatalog",
    "LintResult",
]
