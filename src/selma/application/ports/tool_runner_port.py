"""Tool runner port — abstract interface for running external tools.

Domain depends on this interface, not on implementation.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass

from selma.domain.value_objects.result import Result


@dataclass(frozen=True)
class ToolResult:
    """Structured result from an external tool execution.

    FIXED: P0.2 — Unified field name 'success' (not 'ok').
    """

    tool: str
    success: bool
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        """Backward-compatible alias for success."""
        return self.success


class ToolRunner(ABC):
    """Port: run external lint tools (ruff, pylint, pyright).

    Infrastructure implements this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""
        ...

    @abstractmethod
    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Execute the tool on given paths and return structured result.

        Preconditions:
            - a_paths is a non-empty list of file paths.

        Postconditions:
            Returns Ok with ToolResult, or Failure on execution error.

        Side Effects: Spawns an external process.
        Resource: Subprocess handle.
        Failure: Returns Failure on file-not-found or timeout.
        """
        ...
