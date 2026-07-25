"""Ruff linter and formatter runners."""
from __future__ import annotations

from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner


class RuffCheckRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "ruff"

    def run(self, paths: list[str], *, bin_path: str | None = None, **kwargs: object) -> ToolResult:
        ruff = self._resolve_bin(bin_path)
        if not ruff:
            return ToolResult("ruff", False, "", "ruff not found", 127)
        return self._exec([ruff, "check", *paths])


class RuffFormatRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "ruff"

    def run(self, paths: list[str], *, bin_path: str | None = None, **kwargs: object) -> ToolResult:
        ruff = self._resolve_bin(bin_path)
        if not ruff:
            return ToolResult("ruff", False, "", "ruff not found", 127)
        return self._exec([ruff, "format", "--check", *paths])
