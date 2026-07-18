"""Domain models for the Agent Collaboration Orchestrator.

These are pure data contracts (entities / value objects). They contain no I/O,
no adapter knowledge, and no framework types beyond dataclasses and domain enums.

Implementers must treat field names and types as the public domain API.
Changes require an ADR or explicit domain versioning decision.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import astuple
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Self

from agent_orchestrator.domain.enums import ArtifactKind
from agent_orchestrator.domain.enums import ReviewDecision
from agent_orchestrator.domain.enums import RoleKind
from agent_orchestrator.domain.enums import TaskStatus
from agent_orchestrator.domain.enums import WorkflowStatus
from agent_orchestrator.domain.enums import WorkflowStepStatus


@dataclass(frozen=True)
class BaseEntity:
    """Abstract base for domain dataclass entities.

    Provides shared serialization helpers. Subclasses define fields only.
    Must be frozen so frozen entity subclasses can inherit safely.
    """

    def to_dict(self) -> dict[str, Any]:
        """Convert instance to a dictionary.

        Returns:
            Dict of all attributes.
        """
        result: dict[str, Any] = asdict(self)
        return result

    def to_tuple(self) -> tuple[Any, ...]:
        """Convert instance to a tuple of field values.

        Returns:
            Tuple of field values in definition order.
        """
        result: tuple[Any, ...] = astuple(self)
        return result

    @classmethod
    def from_dict(cls, a_data: dict[str, Any]) -> Self:
        """Create instance from a dictionary.

        Args:
            a_data: Keys matching the entity field names.

        Returns:
            Instance of the calling class.
        """
        result: Self = cls(**a_data)
        return result

    @classmethod
    def from_tuple(cls, a_data: tuple[Any, ...]) -> Self:
        """Create instance from a tuple.

        Args:
            a_data: Values matching field definition order.

        Returns:
            Instance of the calling class.
        """
        result: Self = cls(*a_data)
        return result


@dataclass(frozen=True)
class Role(BaseEntity):
    """A role assigned to agents within a workflow.

    Attributes:
        id: Stable role identifier (config key).
        kind: Canonical role kind.
        description: Human-readable responsibility summary.
        responsibilities: Explicit duty list for this role.
    """

    id: str
    kind: RoleKind
    description: str = ""
    responsibilities: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AgentDefinition(BaseEntity):
    """Configured agent binding (not a runtime process).

    Attributes:
        id: Stable agent identifier (config key).
        adapter: Adapter plugin name (e.g. ``opencode``, ``mimo``).
        role_id: Reference to a ``Role.id``.
        prompt_ref: Optional prompt template reference.
        parameters: Adapter-specific opaque parameters (validated by adapter).
    """

    id: str
    adapter: str
    role_id: str
    prompt_ref: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptTemplate(BaseEntity):
    """Reusable prompt template referenced by agents or tasks.

    Attributes:
        id: Stable prompt identifier.
        content: Template body (engine may support simple substitution later).
        metadata: Optional free-form metadata.
    """

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Task(BaseEntity):
    """A unit of work dispatched to an agent.

    Attributes:
        id: Stable task identifier within a workflow run.
        name: Short display name.
        description: Detailed instruction for the agent.
        agent_id: Agent that should execute this task.
        status: Current task status.
        inputs: Input artifact ids or inline payload keys.
        expected_outputs: Expected artifact kinds or ids.
        prompt_ref: Optional prompt override for this task.
        metadata: Free-form metadata.
    """

    id: str
    name: str
    description: str
    agent_id: str
    status: TaskStatus = TaskStatus.PENDING
    inputs: tuple[str, ...] = field(default_factory=tuple)
    expected_outputs: tuple[str, ...] = field(default_factory=tuple)
    prompt_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewGate(BaseEntity):
    """A gate that pauses the workflow until review criteria are met.

    Attributes:
        id: Stable gate identifier.
        reviewer_agent_id: Agent responsible for the review.
        required_decision: Decision required to pass the gate.
        max_iterations: Max revision loops before hard failure (None = unlimited).
        on_reject: Step id or policy name when rejected (engine-defined semantics).
    """

    id: str
    reviewer_agent_id: str
    required_decision: ReviewDecision = ReviewDecision.APPROVE
    max_iterations: int | None = 3
    on_reject: str | None = None


@dataclass(frozen=True)
class WorkflowStep(BaseEntity):
    """One ordered step in a workflow definition.

    Attributes:
        id: Stable step identifier.
        name: Display name.
        task: Task definition for this step (if executable).
        review_gate: Optional review gate after the task.
        depends_on: Prior step ids that must complete first.
        status: Runtime step status (definition defaults to PENDING).
    """

    id: str
    name: str
    task: Task | None = None
    review_gate: ReviewGate | None = None
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING


@dataclass(frozen=True)
class Workflow(BaseEntity):
    """Ordered workflow definition.

    Attributes:
        id: Stable workflow identifier.
        name: Display name.
        description: Purpose of the workflow.
        steps: Ordered steps (engine may also honor ``depends_on``).
        metadata: Free-form metadata.
    """

    id: str
    name: str
    description: str = ""
    steps: tuple[WorkflowStep, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Artifact(BaseEntity):
    """A durable product of a task or review.

    Attributes:
        id: Stable artifact identifier.
        kind: Classification.
        path: Filesystem path relative to workspace or absolute.
        producer_task_id: Task that produced this artifact.
        content_type: MIME-like or extension hint.
        metadata: Free-form metadata (checksums, sizes, etc. later).
    """

    id: str
    kind: ArtifactKind
    path: str
    producer_task_id: str | None = None
    content_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewResult(BaseEntity):
    """Outcome of a review gate evaluation.

    Attributes:
        gate_id: Review gate that produced this result.
        decision: Review decision.
        summary: Human-readable summary.
        findings: Structured findings (free-form dicts at foundation).
        iteration: Which revision loop this result belongs to.
        reviewer_agent_id: Agent that produced the review.
    """

    gate_id: str
    decision: ReviewDecision
    summary: str
    findings: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    iteration: int = 1
    reviewer_agent_id: str | None = None


@dataclass(frozen=True)
class WorkflowState(BaseEntity):
    """Runtime state of a workflow run.

    Attributes:
        run_id: Unique run identifier.
        workflow_id: Definition id.
        status: Overall run status.
        current_step_id: Step currently executing or awaiting review.
        step_statuses: Map of step id → status name (string for JSON friendliness).
        iteration_counts: Map of gate/step id → iteration count.
        artifact_ids: Artifacts produced so far.
        error_message: Last fatal error if any.
    """

    run_id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step_id: str | None = None
    step_statuses: dict[str, str] = field(default_factory=dict)
    iteration_counts: dict[str, int] = field(default_factory=dict)
    artifact_ids: tuple[str, ...] = field(default_factory=tuple)
    error_message: str | None = None


@dataclass(frozen=True)
class ExecutionContext(BaseEntity):
    """Context passed into an agent execution.

    Attributes:
        run_id: Workflow run id.
        workflow_id: Workflow definition id.
        step_id: Current step id.
        task: Task being executed.
        workspace_path: Root workspace for file operations.
        artifacts: Artifacts available as inputs.
        variables: Engine-supplied variables (paths, prior outputs).
        prompt: Resolved prompt text if any.
    """

    run_id: str
    workflow_id: str
    step_id: str
    task: Task
    workspace_path: str
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)
    variables: dict[str, Any] = field(default_factory=dict)
    prompt: str | None = None


@dataclass(frozen=True)
class ExecutionResult(BaseEntity):
    """Result returned by an agent after executing a task.

    Attributes:
        success: Whether the agent considers the task successful.
        summary: Short summary of work done.
        artifacts: Artifacts produced.
        logs: Optional log lines or log file references.
        exit_code: Process exit code when applicable.
        raw: Opaque adapter payload for debugging (not for core logic).
    """

    success: bool
    summary: str
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)
    logs: tuple[str, ...] = field(default_factory=tuple)
    exit_code: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
