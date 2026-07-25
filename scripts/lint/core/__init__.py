"""Core abstractions for the linter."""

from __future__ import annotations

from scripts.lint.core.result import Result

__all__ = ["LintEngine", "LintVisitor", "Result", "Rule", "Violation"]
