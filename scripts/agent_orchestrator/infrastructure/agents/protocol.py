"""Agent port — the only interface the core may depend on for external agents.

Concrete adapters (OpenCode, Mimo, Poolside, etc.) live outside the core and
implement this protocol. The core never imports vendor SDKs or CLIs directly.
"""

from __future__ import annotations

from typing import Protocol
from typing import runtime_checkable

from agent_orchestrator.domain.models import ExecutionContext
from agent_orchestrator.domain.models import ExecutionResult
from agent_orchestrator.domain.models import Task


@runtime_checkable
class AgentProtocol(Protocol):
    """Plugin contract for an AI coding agent adapter.

    Implementations translate domain tasks into vendor-specific invocations
    (CLI, API, subprocess) and map results back to ``ExecutionResult``.
    """

    @property
    def name(self) -> str:
        r"""Stable adapter name matching ``AgentDefinition.adapter``.

        Returns:
            Adapter registry key (e.g. ``\"opencode\"``, ``\"mimo\"``).
        """
        ...

    def execute(self, a_task: Task, a_context: ExecutionContext) -> ExecutionResult:
        """Execute a task in the given context.

        Args:
            a_task: Domain task to perform.
            a_context: Runtime context (workspace, artifacts, prompt, variables).

        Returns:
            Structured execution result. On failure, ``success`` is False and
            ``summary`` / ``logs`` explain the failure. Prefer returning a result
            over raising for recoverable agent failures; raise only for adapter
            misconfiguration or infrastructure faults.
        """
        ...


@runtime_checkable
class AgentFactoryProtocol(Protocol):
    """Creates agent adapters from configuration.

    Used by infrastructure wiring so the service layer depends only on ports.
    """

    def create(self, a_adapter_name: str, a_parameters: dict[str, object] | None = None) -> AgentProtocol:
        """Instantiate an adapter by registry name.

        Args:
            a_adapter_name: Key from ``AgentDefinition.adapter``.
            a_parameters: Opaque adapter parameters from config.

        Returns:
            Ready-to-use agent adapter.

        Raises:
            AdapterNotRegisteredError: No implementation for ``a_adapter_name``.
        """
        ...
