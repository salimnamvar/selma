"""Base class for external tool runners."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
import shutil
import subprocess

from scripts.lint.core.result import Result


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Structured result from an external tool execution."""

    tool: str
    success: bool
    stdout: str
    stderr: str
    returncode: int

    @property
    def ok(self) -> bool:
        """Alias for success for backward compatibility."""
        return self.success


class ToolRunner(ABC):
    """Abstract base class for external tool runners."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name.

        Precondition: None.
        Postcondition: Returns the tool name string.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: str = ""
        if b_continue:
            b_result = ""
        return b_result

    @abstractmethod
    def run(self, a_paths: list[str], **kwargs: object) -> Result[ToolResult]:
        """Execute the tool on given paths and return structured result.

        Precondition: a_paths is a non-empty list of file paths.
        Postcondition: returns structured tool execution result.
        Side effect: spawns an external process.
        Resource: subprocess handle.
        Failure: returns Result.failure on execution error.
        """
        b_continue = True
        result: Result[ToolResult] = Result.failure("abstract method")
        if b_continue:
            result = Result.failure("abstract method")
        return result

    def _resolve_bin(self, hint: str | None = None) -> Result[str]:
        """Resolve the binary path for this tool.

        Precondition: hint is None or a file path string.
        Postcondition: returns resolved binary path or failure.
        Side effect: queries PATH via shutil.which.
        Resource: none.
        Failure: returns failure when binary not found.
        """
        b_continue = True
        result: Result[str] = Result.failure("binary not found")
        resolved = None
        if hint and (shutil.which(hint) or hint.startswith("/")):
            resolved = hint
        else:
            resolved = shutil.which(self.name)
        if resolved is None:
            b_continue = False
        if b_continue:
            result = Result.success(resolved)
        return result

    def _exec(self, args: list[str], cwd: str | None = None) -> Result[ToolResult]:
        """Execute an external tool as a subprocess.

        Precondition: args is a non-empty command list.
        Postcondition: returns structured tool execution result.
        Side effect: spawns a subprocess.
        Resource: subprocess handle, 300s timeout.
        Failure: returns Result.failure on file-not-found or timeout.
        """
        b_continue = True
        result: Result[ToolResult] = Result.success(
            ToolResult(
                tool=self.name,
                success=False,
                stdout="",
                stderr="",
                returncode=1,
            )
        )
        try:
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300,
                check=False,
            )
        except (
            FileNotFoundError,
            PermissionError,
            OSError,
            subprocess.TimeoutExpired,
        ) as exc:
            b_continue = False
            result = Result.failure(str(exc))
        if b_continue:
            result = Result.success(
                ToolResult(
                    tool=self.name,
                    success=proc.returncode == 0,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    returncode=proc.returncode,
                )
            )
        return result
