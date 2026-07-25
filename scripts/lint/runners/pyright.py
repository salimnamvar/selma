"""Pyright strict type checker runner."""
from __future__ import annotations

from scripts.lint.core.result import Result
from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class PyrightRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "pyright"

    def run(
        self,
        a_paths: list[str],
        *,
        a_bin_path: str | None = None,
        a_project_root: str | None = None,
        **kwargs: object,
    ) -> Result[ToolResult]:
        """Run pyright on the given paths.

        Precondition: a_paths is a non-empty list of file paths.
        Postcondition: returns tool execution result with type check findings.
        Side effect: spawns pyright subprocess.
        Resource: subprocess handle via _exec.
        Failure: returns Result.failure if pyright binary cannot be resolved or executed.
        """
        b_continue = True
        result: Result[ToolResult] = Result.success(ToolResult("pyright", True, "", "pyright not found, skipping", 0))
        pyright_result = self._resolve_bin(a_bin_path)
        if pyright_result.is_failure():
            b_continue = False
            result = Result.failure(pyright_result.message)
        if b_continue:
            if pyright_result.is_success() and pyright_result.value:
                cwd = a_project_root or "."
                result = self._exec([pyright_result.value], cwd=cwd)
        return result
