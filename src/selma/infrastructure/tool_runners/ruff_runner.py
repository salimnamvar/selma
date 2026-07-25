"""Ruff runner — runs ruff check and ruff format.

FIXED: P0.2 — Uses 'success' field consistently.
"""

from __future__ import annotations

from selma.application.ports.tool_runner_port import ToolResult
from selma.domain.value_objects.result import Result
from selma.infrastructure.tool_runners.base_runner import BaseToolRunner


class RuffCheckRunner(BaseToolRunner):
    """Runner for ruff check (linting)."""

    @property
    def name(self) -> str:
        return "ruff"

    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Run ruff check on the given paths."""
        b_continue = True
        result: Result[ToolResult] = Result.failure("unreachable")
        bin_result = self._resolve_bin(str(kwargs.get("a_bin_path", "")))
        if bin_result.is_failure():
            b_continue = False
            result = Result.success(
                ToolResult(
                    tool="ruff",
                    success=True,
                    stdout="",
                    stderr="ruff not found, skipping",
                    returncode=0,
                )
            )
        if b_continue:
            result = self._exec([bin_result.value, "check", *a_paths])
        return result


class RuffFormatRunner(BaseToolRunner):
    """Runner for ruff format (formatting check)."""

    @property
    def name(self) -> str:
        return "ruff"

    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Run ruff format check on the given paths."""
        b_continue = True
        result: Result[ToolResult] = Result.failure("unreachable")
        bin_result = self._resolve_bin(str(kwargs.get("a_bin_path", "")))
        if bin_result.is_failure():
            b_continue = False
            result = Result.success(
                ToolResult(
                    tool="ruff",
                    success=True,
                    stdout="",
                    stderr="ruff not found, skipping",
                    returncode=0,
                )
            )
        if b_continue:
            result = self._exec([bin_result.value, "format", "--check", *a_paths])
        return result
