"""Tool runner port — abstract interface for running external tools.

Domain depends on this interface, not on implementation.
Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.value_objects.result import Result


class ToolResult(BaseModel):
    """Structured result from an external tool execution."""

    model_config = ConfigDict(frozen=True)

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
        """Execute the tool on given paths and return structured result."""
        ...
