"""SC-007, SC-113: Assert validation — no assert for input validation."""
from __future__ import annotations

import ast

from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation

INVALID_RESULT = None


class AssertValidationRule(Rule):
    """SC-007/113: assert shall not be used for input validation."""

    @property
    def code(self) -> str:
        return "SC007"

    @property
    def description(self) -> str:
        return "No assert for input validation"

    def check_Assert(self, a_node: ast.Assert, a_filepath: str) -> list[Violation]:
        """Check that assert is not used for input validation."""
        return [Violation(
            a_filepath, a_node.lineno, a_node.col_offset,
            self.code,
            "assert forbidden for validation; use explicit checks with Result return",
        )]
