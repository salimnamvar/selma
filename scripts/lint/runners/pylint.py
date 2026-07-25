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
        paths: list[str],
        *,
        bin_path: str | None = None,
        rcfile: str | None = None,
        project_root: str | None = None,
        **kwargs: object,
    ) -> ToolResult:
        pylint_bin = self._resolve_bin(bin_path)
        if not pylint_bin:
            return ToolResult("pylint", True, "", "pylint not found, skipping", 0)

        if rcfile is None:
            lint_dir = Path(__file__).resolve().parent.parent
            rcfile = str(lint_dir / "pylintrc")

        if not Path(rcfile).exists():
            return ToolResult("pylint", True, "", f"pylintrc not found at {rcfile}, skipping", 0)

        src = paths[0] if paths else "src"
        return self._exec([pylint_bin, f"--rcfile={rcfile}", "--recursive=y", "--fail-under=8", src])
