"""Domain layer for the Agent Collaboration Orchestrator.

Entities, enums, and exceptions only. No I/O. No framework adapters.
"""

from agent_orchestrator.domain.enums import ArtifactKind
from agent_orchestrator.domain.enums import ReviewDecision
from agent_orchestrator.domain.enums import RoleKind
from agent_orchestrator.domain.enums import TaskStatus
from agent_orchestrator.domain.enums import WorkflowStatus
from agent_orchestrator.domain.enums import WorkflowStepStatus
from agent_orchestrator.domain.exceptions import AdapterNotRegisteredError
from agent_orchestrator.domain.exceptions import AgentExecutionError
from agent_orchestrator.domain.exceptions import AgentNotFoundError
from agent_orchestrator.domain.exceptions import ArtifactError
from agent_orchestrator.domain.exceptions import ConfigurationError
from agent_orchestrator.domain.exceptions import OrchestratorError
from agent_orchestrator.domain.exceptions import ProjectBaseError
from agent_orchestrator.domain.exceptions import ReviewGateError
from agent_orchestrator.domain.exceptions import WorkflowExecutionError
from agent_orchestrator.domain.exceptions import WorkflowNotFoundError
from agent_orchestrator.domain.models import AgentDefinition
from agent_orchestrator.domain.models import Artifact
from agent_orchestrator.domain.models import BaseEntity
from agent_orchestrator.domain.models import ExecutionContext
from agent_orchestrator.domain.models import ExecutionResult
from agent_orchestrator.domain.models import PromptTemplate
from agent_orchestrator.domain.models import ReviewGate
from agent_orchestrator.domain.models import ReviewResult
from agent_orchestrator.domain.models import Role
from agent_orchestrator.domain.models import Task
from agent_orchestrator.domain.models import Workflow
from agent_orchestrator.domain.models import WorkflowState
from agent_orchestrator.domain.models import WorkflowStep

__all__ = [
    "AdapterNotRegisteredError",
    "AgentDefinition",
    "AgentExecutionError",
    "AgentNotFoundError",
    "Artifact",
    "ArtifactError",
    "ArtifactKind",
    "BaseEntity",
    "ConfigurationError",
    "ExecutionContext",
    "ExecutionResult",
    "OrchestratorError",
    "ProjectBaseError",
    "PromptTemplate",
    "ReviewDecision",
    "ReviewGate",
    "ReviewGateError",
    "ReviewResult",
    "Role",
    "RoleKind",
    "Task",
    "TaskStatus",
    "Workflow",
    "WorkflowExecutionError",
    "WorkflowNotFoundError",
    "WorkflowState",
    "WorkflowStatus",
    "WorkflowStep",
    "WorkflowStepStatus",
]
