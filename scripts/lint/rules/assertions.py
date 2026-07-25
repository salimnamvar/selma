"""SC-007, SC-113: Assert validation — no assert for input validation."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation


class AssertValidationRule(Rule):
    """SC-007/113: assert shall not be used for input validation."""

    @property
    def code(self) -> str:
        return "SC007"

    @property
    def description(self) -> str:
        return "No assert for input validation"

    def check_Assert(self, node: ast.Assert, filepath: str) -> list[Violation]:
        return [Violation(
            filepath, node.lineno, node.col_offset,
            self.code,
            "assert forbidden for validation; use explicit checks with Result return",
        )]
