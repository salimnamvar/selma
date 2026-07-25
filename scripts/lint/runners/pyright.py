"""Pyright strict type checker runner."""
from __future__ import annotations

from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class PyrightRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "pyright"

    def run(
        self,
        paths: list[str],
        *,
        bin_path: str | None = None,
        project_root: str | None = None,
        **kwargs: object,
    ) -> ToolResult:
        pyright_bin = self._resolve_bin(bin_path)
        if not pyright_bin:
            return ToolResult("pyright", True, "", "pyright not found, skipping", 0)

        cwd = project_root or "."
        return self._exec([pyright_bin], cwd=cwd)
