"""Repository ports for the Agent Collaboration Orchestrator.

Repositories load and store domain objects. Implementations belong in
infrastructure (YAML files, filesystem, future DB). Services depend on these
protocols only.
"""

from __future__ import annotations

from typing import Protocol

from agent_orchestrator.domain.models import AgentDefinition
from agent_orchestrator.domain.models import Artifact
from agent_orchestrator.domain.models import PromptTemplate
from agent_orchestrator.domain.models import Role
from agent_orchestrator.domain.models import Workflow
from agent_orchestrator.domain.models import WorkflowState


class AgentRepositoryProtocol(Protocol):
    """Loads agent definitions from configuration."""

    def get(self, a_agent_id: str) -> AgentDefinition:
        """Return a single agent definition.

        Args:
            a_agent_id: Agent id.

        Returns:
            Agent definition.

        Raises:
            AgentNotFoundError: Unknown agent id.
        """
        ...

    def list_all(self) -> list[AgentDefinition]:
        """Return all configured agents.

        Returns:
            List of agent definitions.
        """
        ...


class RoleRepositoryProtocol(Protocol):
    """Loads role definitions from configuration."""

    def get(self, a_role_id: str) -> Role:
        """Return a single role.

        Args:
            a_role_id: Role id.

        Returns:
            Role definition.
        """
        ...

    def list_all(self) -> list[Role]:
        """Return all roles.

        Returns:
            List of roles.
        """
        ...


class WorkflowRepositoryProtocol(Protocol):
    """Loads workflow definitions from configuration."""

    def get(self, a_workflow_id: str) -> Workflow:
        """Return a workflow definition.

        Args:
            a_workflow_id: Workflow id.

        Returns:
            Workflow definition.

        Raises:
            WorkflowNotFoundError: Unknown workflow id.
        """
        ...

    def list_all(self) -> list[Workflow]:
        """Return all workflow definitions.

        Returns:
            List of workflows.
        """
        ...


class PromptRepositoryProtocol(Protocol):
    """Loads prompt templates from configuration."""

    def get(self, a_prompt_id: str) -> PromptTemplate:
        """Return a prompt template.

        Args:
            a_prompt_id: Prompt id.

        Returns:
            Prompt template.
        """
        ...


class ArtifactRepositoryProtocol(Protocol):
    """Persists and retrieves workflow artifacts."""

    def save(self, a_artifact: Artifact) -> Artifact:
        """Persist artifact metadata (and optionally content by path).

        Args:
            a_artifact: Artifact to store.

        Returns:
            Stored artifact (may include generated fields).
        """
        ...

    def get(self, a_artifact_id: str) -> Artifact:
        """Load artifact metadata by id.

        Args:
            a_artifact_id: Artifact id.

        Returns:
            Artifact.

        Raises:
            ArtifactError: Not found or unreadable.
        """
        ...

    def list_for_run(self, a_run_id: str) -> list[Artifact]:
        """List artifacts produced by a workflow run.

        Args:
            a_run_id: Workflow run id.

        Returns:
            Artifacts for the run.
        """
        ...


class WorkflowStateRepositoryProtocol(Protocol):
    """Persists workflow run state for resume and audit."""

    def save(self, a_state: WorkflowState) -> WorkflowState:
        """Save or update run state.

        Args:
            a_state: Current state.

        Returns:
            Persisted state.
        """
        ...

    def get(self, a_run_id: str) -> WorkflowState:
        """Load run state.

        Args:
            a_run_id: Run id.

        Returns:
            Workflow state.
        """
        ...
