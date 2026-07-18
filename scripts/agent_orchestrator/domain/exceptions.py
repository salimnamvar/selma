"""Domain exception hierarchy for the Agent Collaboration Orchestrator.

Follow the project pattern: never raise the root base directly; always use a
typed subclass with a stable ``reason`` code.
"""

from __future__ import annotations

from typing import Any


class ProjectBaseError(Exception):
    """Root base for all project exceptions.

    Never raise this class directly — always use a typed subclass.

    Attributes:
        message: Human-readable error description.
        resource_type: Resource type affected.
        resource_name: Resource identifier.
        details: Pre-built error detail objects.
    """

    reason: str = "UNKNOWN_ERROR"

    def __init__(
        self,
        a_message: str,
        a_resource_type: str | None = None,
        a_resource_name: str | None = None,
        a_details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = a_message
        self.resource_type = a_resource_type
        self.resource_name = a_resource_name
        self.details: list[dict[str, Any]] = list(a_details) if a_details else []
        super().__init__(a_message)


class OrchestratorError(ProjectBaseError):
    """Base for orchestrator-specific errors."""

    reason = "ORCHESTRATOR_ERROR"


class ConfigurationError(OrchestratorError):
    """Configuration is missing, invalid, or inconsistent."""

    reason = "CONFIGURATION_ERROR"


class AgentNotFoundError(OrchestratorError):
    """Requested agent id is not registered or not loadable."""

    reason = "AGENT_NOT_FOUND"


class WorkflowNotFoundError(OrchestratorError):
    """Requested workflow id or definition is not found."""

    reason = "WORKFLOW_NOT_FOUND"


class WorkflowExecutionError(OrchestratorError):
    """Workflow execution failed at the engine level."""

    reason = "WORKFLOW_EXECUTION_ERROR"


class AgentExecutionError(OrchestratorError):
    """An agent adapter failed while executing a task."""

    reason = "AGENT_EXECUTION_ERROR"


class ReviewGateError(OrchestratorError):
    """Review gate evaluation or enforcement failed."""

    reason = "REVIEW_GATE_ERROR"


class ArtifactError(OrchestratorError):
    """Artifact load, store, or validation failed."""

    reason = "ARTIFACT_ERROR"


class AdapterNotRegisteredError(OrchestratorError):
    """No adapter implementation is registered for the requested adapter name."""

    reason = "ADAPTER_NOT_REGISTERED"
