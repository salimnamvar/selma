"""Lint engine: orchestrates file reading, AST parsing, and rule dispatch."""
from __future__ import annotations

import ast
import fnmatch
import logging
from pathlib import Path

from scripts.lint.core.result import INVALID_RESULT
from scripts.lint.core.result import Result
from scripts.lint.core.visitor import LintVisitor
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.config import LintConfig

logger = logging.getLogger(__name__)


class LintEngine:
    def __init__(self, rules: list[Rule], config: LintConfig | None = None) -> None:
        self._all_rules = rules
        self._config = config or LintConfig()
        self._exclude_paths = tuple(self._config.exclude.paths)

    def _is_excluded(self, filepath: str) -> Result[bool]:
        """Check whether filepath matches any configured exclusion pattern.

        Precondition: filepath is a non-empty string.
        Postcondition: returns Ok(True) if excluded, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[bool] = Result.success(False)
        for pattern in self._exclude_paths:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filepath, f"*/{pattern}/*"):
                b_continue = False
                result = Result.success(True)
        if b_continue:
            result = Result.success(False)
        return result

    def _rules_for_file(self, filepath: str) -> Result[list[Rule]]:
        """Return the list of rules applicable to the given filepath.

        Precondition: filepath is a non-empty string.
        Postcondition: returns Ok with filtered rule list.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[list[Rule]]
        excluded_codes = set(self._config.exclude.codes)
        if not excluded_codes:
            b_continue = False
            result = Result.success(self._all_rules)
        if b_continue:
            result = Result.success([r for r in self._all_rules if r.code not in excluded_codes])
        return result

    def lint_file(self, a_filepath: str | Path) -> Result[list[Violation]]:
        """Lint a single Python file and return violations.

        Precondition: a_filepath points to an existing Python file.
        Postcondition: returns Ok with list of violations found.
        Side effect: logs warnings on read or parse failures.
        Resource: reads file content from disk.
        Failure: returns Ok with IO_ERROR or PARSE violation on read errors.
        """
        a_filepath = str(a_filepath)
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]]
        excluded = self._is_excluded(a_filepath)
        is_excluded = excluded.is_success() and excluded.value
        if not is_excluded:
            try:
                source = Path(a_filepath).read_text(encoding="utf-8")
            except OSError as exc:
                b_continue = False
                logger.warning("Failed to read %s: %s", a_filepath, exc)
                violations = [Violation(a_filepath, 0, 0, "IO_ERROR", str(exc), "error")]
            if b_continue:
                try:
                    tree = ast.parse(source, filename=a_filepath)
                except (SyntaxError, UnicodeDecodeError) as exc:
                    b_continue = False
                    violations = [Violation(a_filepath, 0, 0, "PARSE", str(exc), "error")]
                if b_continue:
                    rules_result = self._rules_for_file(a_filepath)
                    if rules_result.is_success():
                        visitor = LintVisitor(rules_result.value, a_filepath)
                        visitor.visit(tree)
                        violations = visitor.violations
        result = Result.success(violations)
        return result

    def lint_paths(self, a_paths: list[str | Path]) -> Result[list[Violation]]:
        """Lint multiple file or directory paths and return all violations.

        Precondition: a_paths is a non-empty list of file or directory paths.
        Postcondition: returns Ok with combined list of violations.
        Side effect: none.
        Resource: delegates to lint_file for each Python file.
        Failure: returns Ok with empty list if no violations found.
        """
        b_continue = True
        violations: list[Violation] = []
        result: Result[list[Violation]]
        if b_continue:
            for path in a_paths:
                p = Path(path)
                if p.is_file() and p.suffix == ".py":
                    file_result = self.lint_file(p)
                    if file_result.is_success():
                        violations.extend(file_result.value)
                elif p.is_dir():
                    for py_file in sorted(p.rglob("*.py")):
                        file_result = self.lint_file(py_file)
                        if file_result.is_success():
                            violations.extend(file_result.value)
        result = Result.success(violations)
        return result
