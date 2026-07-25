"""SC-041, SC-042, SC-052: Error handling rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import get_visitor



class SpecificExceptionRule(Rule):
    """SC-041: All except clauses must catch specific exception types."""

    @property
    def code(self) -> str:
        return "SC041"

    @property
    def description(self) -> str:
        return "Specific exception types in except clauses"

    def _is_last_handler(self, a_node: ast.ExceptHandler) -> bool:
        visitor = get_visitor()
        if not visitor:
            return False
        for parent in reversed(visitor._parent_stack):
            if isinstance(parent, ast.Try):
                handlers = parent.handlers
                if handlers and handlers[-1] is a_node:
                    return True
                return False
        return False

    def check_ExceptHandler(self, a_node: ast.ExceptHandler, a_filepath: str) -> list[Violation]:
        """Check that except clauses catch specific exception types."""
        violations: list[Violation] = []
        if a_node.type is None:
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                "Bare 'except:' forbidden; catch specific exception types",
            )]
        elif isinstance(a_node.type, ast.Name) and a_node.type.id == "Exception":
            if not self._is_last_handler(a_node):
                violations = [Violation(
                    a_filepath, a_node.lineno, a_node.col_offset,
                    self.code,
                    "Broad 'except Exception' forbidden; catch specific types",
                )]
        return violations


class NoSilentFailureRule(Rule):
    """SC-042: No empty except blocks (silent failures).
    Limitation: cannot detect except blocks that don't convert to Result or log
    without full dataflow analysis. Only catches empty/pass-only blocks."""

    @property
    def code(self) -> str:
        return "SC042"

    @property
    def description(self) -> str:
        return "No silent failures (empty except blocks)"

    def check_ExceptHandler(self, a_node: ast.ExceptHandler, a_filepath: str) -> list[Violation]:
        """Check that except blocks are not empty or pass-only."""
        violations: list[Violation] = []
        if not a_node.body:
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                "Empty except block: silent failure forbidden",
            )]
        elif len(a_node.body) == 1 and isinstance(a_node.body[0], ast.Pass):
            violations = [Violation(
                a_filepath, a_node.lineno, a_node.col_offset,
                self.code,
                "Except block contains only 'pass': silent failure forbidden",
            )]
        return violations


class NoReraiseRule(Rule):
    """SC-052: Caught exceptions must not be re-raised."""

    @property
    def code(self) -> str:
        return "SC052"

    @property
    def description(self) -> str:
        return "No exception re-raising"

    def check_ExceptHandler(self, a_node: ast.ExceptHandler, a_filepath: str) -> list[Violation]:
        """Check that caught exceptions are not re-raised."""
        violations: list[Violation] = []
        for child in ast.walk(a_node):
            if isinstance(child, ast.Raise) and child.exc is None:
                violations = [Violation(
                    a_filepath, child.lineno, child.col_offset,
                    self.code,
                    "Re-raise forbidden; convert exception to Result return",
                )]
                break
        return violations
