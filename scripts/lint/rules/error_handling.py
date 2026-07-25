"""SC-041, SC-042, SC-052: Error handling rules."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class SpecificExceptionRule(Rule):
    """SC-041: All except clauses must catch specific exception types."""

    @property
    def code(self) -> str:
        return "SC041"

    @property
    def description(self) -> str:
        return "Specific exception types in except clauses"

    def check_ExceptHandler(self, node: ast.ExceptHandler, filepath: str) -> list[Violation]:
        if node.type is None:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                "Bare 'except:' forbidden; catch specific exception types",
            )]
        if isinstance(node.type, ast.Name) and node.type.id == "Exception":
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                "Broad 'except Exception' forbidden; catch specific types",
            )]
        return []


class NoSilentFailureRule(Rule):
    """SC-042: No empty except blocks (silent failures)."""

    @property
    def code(self) -> str:
        return "SC042"

    @property
    def description(self) -> str:
        return "No silent failures (empty except blocks)"

    def check_ExceptHandler(self, node: ast.ExceptHandler, filepath: str) -> list[Violation]:
        if not node.body:
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                "Empty except block: silent failure forbidden",
            )]
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            return [Violation(
                filepath, node.lineno, node.col_offset,
                self.code,
                "Except block contains only 'pass': silent failure forbidden",
            )]
        return []


class NoReraiseRule(Rule):
    """SC-052: Caught exceptions must not be re-raised."""

    @property
    def code(self) -> str:
        return "SC052"

    @property
    def description(self) -> str:
        return "No exception re-raising"

    def check_ExceptHandler(self, node: ast.ExceptHandler, filepath: str) -> list[Violation]:
        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc is None:
                return [Violation(
                    filepath, child.lineno, child.col_offset,
                    self.code,
                    "Re-raise forbidden; convert exception to Result return",
                )]
        return []
