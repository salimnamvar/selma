"""Pylint runner with Google pylintrc."""
from __future__ import annotations

from pathlib import Path

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
    ) -> ToolResult:
        """Run pylint on the given paths."""
        pylint_bin = self._resolve_bin(a_bin_path)
        rcfile = a_rcfile
        result = ToolResult("pylint", True, "", "pylint not found, skipping", 0)
        if pylint_bin:
            if rcfile is None:
                lint_dir = Path(__file__).resolve().parent.parent
                rcfile = str(lint_dir / "pylintrc")
            if not Path(rcfile).exists():
                result = ToolResult("pylint", True, "", f"pylintrc not found at {rcfile}, skipping", 0)
            else:
                src = a_paths[0] if a_paths else "src"
                result = self._exec([pylint_bin, f"--rcfile={rcfile}", "--recursive=y", "--fail-under=8", src])
        return result
