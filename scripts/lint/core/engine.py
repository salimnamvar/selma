from __future__ import annotations

import ast
import fnmatch
import sys
from pathlib import Path

from scripts.lint.core.visitor import LintVisitor
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import LintConfig

INVALID_RESULT = None


class LintEngine:
    def __init__(self, rules: list[Rule], config: LintConfig | None = None) -> None:
        self._all_rules = rules
        self._config = config or LintConfig()
        self._exclude_paths = tuple(self._config.exclude.paths)

    def _is_excluded(self, filepath: str) -> bool:
        for pattern in self._exclude_paths:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filepath, f"*/{pattern}/*"):
                return True
        return False

    def _rules_for_file(self, filepath: str) -> list[Rule]:
        excluded_codes = set(self._config.exclude.codes)
        if not excluded_codes:
            return self._all_rules
        return [r for r in self._all_rules if r.code not in excluded_codes]

    def lint_file(self, a_filepath: str | Path) -> list[Violation]:
        """Lint a single Python file and return violations."""
        a_filepath = str(a_filepath)
        violations: list[Violation] = []
        if not self._is_excluded(a_filepath):
            try:
                source = Path(a_filepath).read_text(encoding="utf-8")
                tree = ast.parse(source, filename=a_filepath)
            except (SyntaxError, UnicodeDecodeError) as exc:
                violations = [Violation(a_filepath, 0, "PARSE", str(exc), "error")]
            else:
                rules = self._rules_for_file(a_filepath)
                visitor = LintVisitor(rules, a_filepath)
                visitor.visit(tree)
                violations = visitor.violations
        return violations

    def lint_paths(self, a_paths: list[str | Path]) -> list[Violation]:
        """Lint multiple file or directory paths and return all violations."""
        violations: list[Violation] = []
        for path in a_paths:
            p = Path(path)
            if p.is_file() and p.suffix == ".py":
                violations.extend(self.lint_file(p))
            elif p.is_dir():
                for py_file in sorted(p.rglob("*.py")):
                    violations.extend(self.lint_file(py_file))
        return violations
