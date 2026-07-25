"""Ruff linter and formatter runners."""

from __future__ import annotations

from scripts.lint.core.result import Result
from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class RuffCheckRunner(ToolRunner):
    """Runner for ruff check (linting)."""

    @property
    def name(self) -> str:
        """Human-readable tool name.

        Precondition: None.
        Postcondition: Returns the tool name string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "ruff"
        return b_result

    def run(
        self, a_paths: list[str], *, a_bin_path: str | None = None, **kwargs: object
    ) -> Result[ToolResult]:
        """Run ruff check on the given paths.

        Precondition: a_paths is a non-empty list of file paths.
        Postcondition: returns tool execution result with lint findings.
        Side effect: spawns ruff subprocess.
        Resource: subprocess handle via _exec.
        Failure: returns Result.failure if ruff binary cannot be resolved or executed.
        """
        b_continue = True
        result: Result[ToolResult] = Result.success(
            ToolResult(
                tool="ruff",
                ok=False,
                stdout="",
                stderr="ruff not found",
                returncode=127,
            )
        )
        ruff_result = self._resolve_bin(a_bin_path)
        if ruff_result.is_failure().value:
            b_continue = False
            result = Result.failure(ruff_result.message)
        if b_continue and ruff_result.is_success().value and ruff_result.value:
            result = self._exec([ruff_result.value, "check", *a_paths])
        return result


class RuffFormatRunner(ToolRunner):
    """Runner for ruff format (formatting check)."""

    @property
    def name(self) -> str:
        """Human-readable tool name.

        Precondition: None.
        Postcondition: Returns the tool name string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = "ruff"
        return b_result

    def run(
        self, a_paths: list[str], *, a_bin_path: str | None = None, **kwargs: object
    ) -> Result[ToolResult]:
        """Run ruff format check on the given paths.

        Precondition: a_paths is a non-empty list of file paths.
        Postcondition: returns tool execution result with format findings.
        Side effect: spawns ruff subprocess.
        Resource: subprocess handle via _exec.
        Failure: returns Result.failure if ruff binary cannot be resolved or executed.
        """
        b_continue = True
        result: Result[ToolResult] = Result.success(
            ToolResult(
                tool="ruff",
                ok=False,
                stdout="",
                stderr="ruff not found",
                returncode=127,
            )
        )
        ruff_result = self._resolve_bin(a_bin_path)
        if ruff_result.is_failure().value:
            b_continue = False
            result = Result.failure(ruff_result.message)
        if b_continue and ruff_result.is_success().value and ruff_result.value:
            result = self._exec([ruff_result.value, "format", "--check", *a_paths])
        return result
