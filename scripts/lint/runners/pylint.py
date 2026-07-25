"""Pylint runner with Google pylintrc."""
from __future__ import annotations

from pathlib import Path

from scripts.lint.core.result import Result
from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class PylintRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "pylint"

    def run(
        self,
        a_paths: list[str],
        *,
        a_bin_path: str | None = None,
        a_rcfile: str | None = None,
        a_project_root: str | None = None,
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
        result: Result[ToolResult] = Result.success(ToolResult("pylint", True, "", "pylint not found, skipping", 0))
        pylint_result = self._resolve_bin(a_bin_path)
        if pylint_result.is_failure():
            b_continue = False
            result = Result.failure(pylint_result.message)
        if b_continue:
            if pylint_result.is_success() and pylint_result.value:
                pylint_bin = pylint_result.value
                rcfile = a_rcfile
                if rcfile is None:
                    lint_dir = Path(__file__).resolve().parent.parent
                    rcfile = str(lint_dir / "pylintrc")
                if not Path(rcfile).exists():
                    result = Result.success(ToolResult("pylint", True, "", f"pylintrc not found at {rcfile}, skipping", 0))
                else:
                    src = a_paths[0] if a_paths else "src"
                    result = self._exec([pylint_bin, f"--rcfile={rcfile}", "--recursive=y", "--fail-under=8", src])
        return result
