"""Pyright runner — runs pyright strict type checker.

FIXED: P0.2 — Uses 'success' field consistently.
"""

from __future__ import annotations

from selma.infrastructure.tool_runners.base_runner import BaseToolRunner
from selma.domain.value_objects.result import Result
from selma.application.ports.tool_runner_port import ToolResult


class PyrightRunner(BaseToolRunner):
    """Runner for pyright strict type checker."""

    @property
    def name(self) -> str:
        return "pyright"

    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Run pyright on the given paths."""
        b_continue = True
        result: Result[ToolResult] = Result.failure("unreachable")
        bin_result = self._resolve_bin(str(kwargs.get("a_bin_path", "")))
        if bin_result.is_failure():
            b_continue = False
            result = Result.success(
                ToolResult(
                    tool="pyright",
                    success=True,
                    stdout="",
                    stderr="pyright not found, skipping",
                    returncode=0,
                )
            )
        if b_continue:
            cwd = str(kwargs.get("a_project_root", "."))
            result = self._exec([bin_result.value], a_cwd=cwd)
        return result
