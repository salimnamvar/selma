"""Pylint runner — runs pylint with Google pylintrc.

FIXED: P0.2 — Uses 'success' field consistently.
"""

from __future__ import annotations

from pathlib import Path

from selma.application.ports.tool_runner_port import ToolResult
from selma.domain.value_objects.result import Result
from selma.infrastructure.tool_runners.base_runner import BaseToolRunner


class PylintRunner(BaseToolRunner):
    """Runner for pylint static analysis."""

    @property
    def name(self) -> str:
        return "pylint"

    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Run pylint on the given paths."""
        b_continue = True
        result: Result[ToolResult] = Result.failure("unreachable")
        bin_result = self._resolve_bin(str(kwargs.get("a_bin_path", "")))
        if bin_result.is_failure():
            b_continue = False
            result = Result.success(
                ToolResult(
                    tool="pylint",
                    success=True,
                    stdout="",
                    stderr="pylint not found, skipping",
                    returncode=0,
                )
            )
        if b_continue:
            rcfile = str(kwargs.get("a_rcfile", ""))
            if not rcfile:
                lint_dir = Path(__file__).resolve().parent.parent
                rcfile = str(lint_dir / "pylintrc")
            if not Path(rcfile).exists():
                b_continue = False
                result = Result.success(
                    ToolResult(
                        tool="pylint",
                        success=True,
                        stdout="",
                        stderr=f"pylintrc not found at {rcfile}, skipping",
                        returncode=0,
                    )
                )
        if b_continue:
            src = a_paths[0] if a_paths else "src"
            result = self._exec(
                [
                    bin_result.value,
                    f"--rcfile={rcfile}",
                    "--recursive=y",
                    "--fail-under=8",
                    src,
                ]
            )
        return result
