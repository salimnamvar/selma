"""Base tool runner — common infrastructure for external tool execution.

FIXED: P0.3 — Catches all OSError subtypes, not just FileNotFoundError.
FIXED: P0.2 — Uses 'success' field consistently.
"""

from __future__ import annotations

import logging
import shutil
import subprocess

from selma.application.ports.tool_runner_port import ToolResult
from selma.application.ports.tool_runner_port import ToolRunner
from selma.domain.value_objects.result import Result

logger = logging.getLogger(__name__)


class BaseToolRunner(ToolRunner):
    """Base class for external tool runners.

    Provides common _resolve_bin() and _exec() methods.
    """

    def _resolve_bin(self, a_hint: str | None = None) -> Result[str]:
        """Resolve the binary path for this tool.

        Preconditions: None.
        Postconditions: Returns Ok with binary path, or Failure if not found.
        Side Effect: Queries PATH via shutil.which.
        Resource: None.
        Failure: Returns Failure when binary not found.
        """
        b_continue = True
        result: Result[str] = Result.failure("binary not found")
        resolved = None
        if b_continue and a_hint and (shutil.which(a_hint) or a_hint.startswith("/")):
            b_continue = False
            result = Result.success(a_hint)
        if b_continue:
            resolved = shutil.which(self.name)
            if resolved is None:
                b_continue = False
                result = Result.failure(f"{self.name} not found in PATH")
        if b_continue:
            assert resolved is not None
            result = Result.success(resolved)
        return result

    def _exec(self, a_args: list[str], a_cwd: str | None = None) -> Result[ToolResult]:
        """Execute an external tool as a subprocess.

        FIXED: P0.3 — Catches all OSError subtypes.

        Preconditions:
            - a_args is a non-empty command list.

        Postconditions:
            Returns Ok with ToolResult, or Failure on error.

        Side Effect: Spawns a subprocess.
        Resource: Subprocess handle, 300s timeout.
        Failure: Returns Failure on file-not-found, permission error, or timeout.
        """
        b_continue = True
        result: Result[ToolResult] = Result.failure("unreachable")
        try:
            proc = subprocess.run(
                a_args,
                capture_output=True,
                text=True,
                cwd=a_cwd,
                timeout=300,
                check=False,
            )
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
        except (
            FileNotFoundError,
            PermissionError,
            OSError,
            subprocess.TimeoutExpired,
        ) as exc:
            if b_continue:
                logger.warning("Tool execution failed: %s", exc)
                b_continue = False
                result = Result.failure(str(exc))
        return result
