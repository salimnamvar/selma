from __future__ import annotations

import ast
import fnmatch
import sys
from pathlib import Path

from scripts.lint.core.visitor import LintVisitor
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import LintConfig


class LintEngine:
    def __init__(self, rules: list[Rule], config: LintConfig | None = None) -> None:
        self.rules = rules
        self._exclude_paths = tuple(
            p for p in (config or LintConfig()).exclude.paths
        )

    def _is_excluded(self, filepath: str) -> bool:
        for pattern in self._exclude_paths:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filepath, f"*/{pattern}/*"):
                return True
        return False

    def lint_file(self, filepath: str | Path) -> list[Violation]:
        filepath = str(filepath)
        if self._is_excluded(filepath):
            return []
        try:
            source = Path(filepath).read_text(encoding="utf-8")
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError) as exc:
            return [Violation(filepath, 0, "PARSE", str(exc), "error")]

        visitor = LintVisitor(self.rules, filepath)
        visitor.visit(tree)
        return visitor.violations

    def lint_paths(self, paths: list[str | Path]) -> list[Violation]:
        violations: list[Violation] = []
        for path in paths:
            p = Path(path)
            if p.is_file() and p.suffix == ".py":
                violations.extend(self.lint_file(p))
            elif p.is_dir():
                for py_file in sorted(p.rglob("*.py")):
                    violations.extend(self.lint_file(py_file))
        return violations
