"""Ruff linter and formatter runners."""
from __future__ import annotations

from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner

INVALID_RESULT = None


class RuffCheckRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "ruff"

    def run(self, a_paths: list[str], *, a_bin_path: str | None = None, **kwargs: object) -> ToolResult:
        """Run ruff check on the given paths."""
        ruff = self._resolve_bin(a_bin_path)
        if ruff:
            result = self._exec([ruff, "check", *a_paths])
        else:
            result = ToolResult("ruff", False, "", "ruff not found", 127)
        return result


class RuffFormatRunner(ToolRunner):
    @property
    def name(self) -> str:
        return "ruff"

    def run(self, a_paths: list[str], *, a_bin_path: str | None = None, **kwargs: object) -> ToolResult:
        """Run ruff format check on the given paths."""
        ruff = self._resolve_bin(a_bin_path)
        if ruff:
            result = self._exec([ruff, "format", "--check", *a_paths])
        else:
            result = ToolResult("ruff", False, "", "ruff not found", 127)
        return result
