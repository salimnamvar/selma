"""Lint engine: orchestrates file reading, AST parsing, and rule dispatch."""

from __future__ import annotations

import ast
import fnmatch
import logging
from pathlib import Path

from scripts.lint.config import LintConfig
from scripts.lint.core.ports import ASTParserPort
from scripts.lint.core.ports import FileLoaderPort
from scripts.lint.core.result import Result
from scripts.lint.core.rule import Rule
from scripts.lint.core.violation import Violation
from scripts.lint.core.visitor import LintVisitor
from scripts.lint.infrastructure.adapters import FilesystemFileLoader
from scripts.lint.infrastructure.adapters import StandardASTParser

logger = logging.getLogger(__name__)


class LintEngine:
    """Orchestrates file reading, AST parsing, and rule dispatch."""

    def __init__(
        self,
        rules: list[Rule],
        config: LintConfig | None = None,
        file_loader: FileLoaderPort | None = None,
        ast_parser: ASTParserPort | None = None,
    ) -> None:
        self._all_rules = rules
        self._config = config or LintConfig()
        self._exclude_paths = tuple(self._config.exclude.paths)
        self.file_loader = file_loader or FilesystemFileLoader()
        self.ast_parser = ast_parser or StandardASTParser()

    def _is_excluded(self, filepath: str) -> Result[bool]:
        """Check whether filepath matches any configured exclusion pattern.

        Precondition: filepath is a non-empty string.
        Postcondition: returns Ok(True) if excluded, Ok(False) otherwise.
        Side effect: none.
        Resource: none.
        Failure: never fails.
        """
        b_continue = True
        result: Result[bool] = Result.success(a_value=False)
        for pattern in self._exclude_paths:
            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(
                filepath, f"*/{pattern}/*"
            ):
                b_continue = False
                result = Result.success(a_value=True)
        if b_continue:
            result = Result.success(a_value=False)
        return result

    def _rules_for_file(self, _filepath: str) -> Result[list[Rule]]:
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
            result = Result.success(
                [r for r in self._all_rules if r.code not in excluded_codes]
            )
        return result

    def lint_file(self, a_filepath: str | Path) -> Result[list[Violation]]:
        """Lint a single Python file and return violations.

        Precondition: a_filepath points to an existing Python file.
        Postcondition: returns Ok with list of violations found.
        Side effect: logs warnings on read or parse failures.
        Resource: reads file content via file_loader port.
        Failure: returns Ok with IO_ERROR or PARSE violation on read errors.
        """
        a_filepath = str(a_filepath)
        b_continue = True
        violations: list[Violation] = []
        excluded = self._is_excluded(a_filepath)
        is_excluded = excluded.is_success().value and excluded.value
        if not is_excluded:
            source_result = self.file_loader.read_source(a_filepath)
            if source_result.is_failure().value:
                b_continue = False
                logger.warning(
                    "Failed to read %s: %s", a_filepath, source_result.message
                )
                violations = [
                    Violation(
                        a_filepath, 0, 0, "IO_ERROR", source_result.message, "error"
                    )
                ]

            if b_continue:
                tree_result = self.ast_parser.parse_ast(source_result.value, a_filepath)
                if tree_result.is_failure().value:
                    b_continue = False
                    violations = [
                        Violation(
                            a_filepath, 0, 0, "PARSE", tree_result.message, "error"
                        )
                    ]

                if b_continue and tree_result.value:
                    rules_result = self._rules_for_file(a_filepath)
                    if rules_result.is_success().value:
                        visitor = LintVisitor(rules_result.value, a_filepath)
                        visitor.visit(tree_result.value)
                        violations = visitor.violations
        return Result.success(violations)

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
                    if file_result.is_success().value:
                        violations.extend(file_result.value)
                elif p.is_dir():
                    for py_file in sorted(p.rglob("*.py")):
                        file_result = self.lint_file(py_file)
                        if file_result.is_success().value:
                            violations.extend(file_result.value)
        result = Result.success(violations)
        return result
