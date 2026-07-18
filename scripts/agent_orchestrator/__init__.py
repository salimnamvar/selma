"""AI Agent Collaboration Orchestrator — foundation package.

Public exports are domain contracts and ports only. Concrete services and
adapters are added in later phases without changing this public surface
unless versioned deliberately.
"""

from agent_orchestrator.domain import AgentDefinition
from agent_orchestrator.domain import Artifact
from agent_orchestrator.domain import ExecutionContext
from agent_orchestrator.domain import ExecutionResult
from agent_orchestrator.domain import ReviewResult
from agent_orchestrator.domain import Role
from agent_orchestrator.domain import Task
from agent_orchestrator.domain import Workflow
from agent_orchestrator.domain import WorkflowState
from agent_orchestrator.infrastructure.agents import AgentProtocol
from agent_orchestrator.infrastructure.config import OrchestratorSettings

__version__ = "0.1.0"

__all__ = [
    "AgentDefinition",
    "AgentProtocol",
    "Artifact",
    "ExecutionContext",
    "ExecutionResult",
    "OrchestratorSettings",
    "ReviewResult",
    "Role",
    "Task",
    "Workflow",
    "WorkflowState",
    "__version__",
]
