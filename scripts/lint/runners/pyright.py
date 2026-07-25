"""Pyright strict type checker runner."""
from __future__ import annotations

from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner

INVALID_RESULT = None


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
    ) -> ToolResult:
        """Run pyright on the given paths."""
        pyright_bin = self._resolve_bin(a_bin_path)
        if pyright_bin:
            cwd = a_project_root or "."
            result = self._exec([pyright_bin], cwd=cwd)
        else:
            result = ToolResult("pyright", True, "", "pyright not found, skipping", 0)
        return result
