"""Application service ports for the Agent Collaboration Orchestrator.

These protocols define use-case boundaries. Implementations are added in later
phases; controllers depend on these ports, not concrete classes.
"""

from __future__ import annotations

from typing import Protocol

from agent_orchestrator.domain.models import ExecutionResult
from agent_orchestrator.domain.models import ReviewResult
from agent_orchestrator.domain.models import Task
from agent_orchestrator.domain.models import WorkflowState


class WorkflowExecutionServiceProtocol(Protocol):
    """Runs and advances workflows."""

    def start(self, a_workflow_id: str, a_workspace_path: str) -> WorkflowState:
        """Start a new workflow run.

        Args:
            a_workflow_id: Workflow definition id.
            a_workspace_path: Root path for artifacts and agent work.

        Returns:
            Initial workflow state for the new run.
        """
        ...

    def advance(self, a_run_id: str) -> WorkflowState:
        """Advance a run to the next eligible step.

        Args:
            a_run_id: Existing run id.

        Returns:
            Updated workflow state.
        """
        ...

    def get_state(self, a_run_id: str) -> WorkflowState:
        """Return current run state.

        Args:
            a_run_id: Run id.

        Returns:
            Current state.
        """
        ...


class AgentCoordinationServiceProtocol(Protocol):
    """Routes tasks to agents and collects results."""

    def dispatch(self, a_task: Task, a_run_id: str) -> ExecutionResult:
        """Dispatch a task to the bound agent.

        Args:
            a_task: Task to execute.
            a_run_id: Owning workflow run.

        Returns:
            Agent execution result.
        """
        ...


class ArtifactManagementServiceProtocol(Protocol):
    """Registers and resolves artifacts for a run."""

    def register(self, a_run_id: str, a_path: str, a_kind: str, a_producer_task_id: str | None = None) -> str:
        """Register an artifact and return its id.

        Args:
            a_run_id: Workflow run id.
            a_path: Artifact path.
            a_kind: Artifact kind name (maps to ``ArtifactKind``).
            a_producer_task_id: Optional producing task id.

        Returns:
            Artifact id.
        """
        ...

    def list_ids(self, a_run_id: str) -> list[str]:
        """List artifact ids for a run.

        Args:
            a_run_id: Workflow run id.

        Returns:
            Artifact ids.
        """
        ...


class ReviewGateServiceProtocol(Protocol):
    """Evaluates review gates and iteration policy."""

    def evaluate(self, a_run_id: str, a_gate_id: str) -> ReviewResult:
        """Run the review gate for a step.

        Args:
            a_run_id: Workflow run id.
            a_gate_id: Review gate id.

        Returns:
            Review result including decision and findings.
        """
        ...

    def should_iterate(self, a_run_id: str, a_gate_id: str, a_result: ReviewResult) -> bool:
        """Decide whether another revision loop is allowed.

        Args:
            a_run_id: Workflow run id.
            a_gate_id: Review gate id.
            a_result: Latest review result.

        Returns:
            True if the engine should re-run the producing step.
        """
        ...
