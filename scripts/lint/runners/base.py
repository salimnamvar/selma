"""Base class for external tool runners."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
import shutil
import subprocess

INVALID_RESULT = None


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool: str
    ok: bool
    stdout: str
    stderr: str
    returncode: int


class ToolRunner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""

    @abstractmethod
    def run(self, a_paths: list[str], **kwargs: object) -> ToolResult:
        """Execute the tool on given paths and return structured result."""

    def _resolve_bin(self, hint: str | None = None) -> str | None:
        if hint and (shutil.which(hint) or hint.startswith("/")):
            return hint
        return shutil.which(self.name)

    def _exec(self, args: list[str], cwd: str | None = None) -> ToolResult:
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300,
            )
            return ToolResult(
                tool=self.name,
                ok=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
        except FileNotFoundError:
            return ToolResult(
                tool=self.name,
                ok=False,
                stdout="",
                stderr=f"{self.name} not found: {args[0]}",
                returncode=127,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                tool=self.name,
                ok=False,
                stdout="",
                stderr=f"{self.name} timed out after 300s",
                returncode=124,
            )
