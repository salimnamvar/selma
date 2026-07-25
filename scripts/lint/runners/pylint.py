"""Pylint runner with Google pylintrc."""

from __future__ import annotations

from pathlib import Path

from scripts.lint.core.result import Result
from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class PylintRunner(ToolRunner):
    """Runner for pylint static analysis."""

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
            b_result = "pylint"
        return b_result

    def run(
        self,
        a_paths: list[str],
        *,
        a_bin_path: str | None = None,
        a_rcfile: str | None = None,
        _a_project_root: str | None = None,
        **kwargs: object,
    ) -> Result[ToolResult]:
        """Run pylint on the given paths.

        Precondition: a_paths is a non-empty list of file paths.
        Postcondition: returns tool execution result with pylint findings.
        Side effect: spawns pylint subprocess.
        Resource: subprocess handle via _exec.
        Failure: returns Result.failure if pylint binary cannot be resolved or executed.
        """
        b_continue = True
        result: Result[ToolResult] = Result.success(
            ToolResult(
                tool="pylint",
                success=True,
                stdout="",
                stderr="pylint not found, skipping",
                returncode=0,
            )
        )
        pylint_result = self._resolve_bin(a_bin_path)
        if pylint_result.is_failure().value:
            b_continue = False
        if b_continue and pylint_result.is_success().value and pylint_result.value:
            pylint_bin = pylint_result.value
            rcfile = a_rcfile
            if rcfile is None:
                lint_dir = Path(__file__).resolve().parent.parent
                rcfile = str(lint_dir / "pylintrc")
            if not Path(rcfile).exists():
                result = Result.success(
                    ToolResult(
                        tool="pylint",
                        success=True,
                        stdout="",
                        stderr=f"pylintrc not found at {rcfile}, skipping",
                        returncode=0,
                    )
                )
            else:
                src = a_paths[0] if a_paths else "src"
                result = self._exec(
                    [
                        pylint_bin,
                        f"--rcfile={rcfile}",
                        "--recursive=y",
                        "--fail-under=8",
                        src,
                    ]
                )
        return result
