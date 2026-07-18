"""Domain enums for the Agent Collaboration Orchestrator.

These are stable contracts. Implementations must not invent parallel status
types; extend via ADR if new lifecycle states are required.
"""

from __future__ import annotations

from enum import Enum
from enum import auto


class WorkflowStepStatus(Enum):
    """Lifecycle status of a single workflow step."""

    PENDING = auto()
    RUNNING = auto()
    AWAITING_REVIEW = auto()
    APPROVED = auto()
    REJECTED = auto()
    FAILED = auto()
    SKIPPED = auto()
    COMPLETED = auto()


class WorkflowStatus(Enum):
    """Lifecycle status of an entire workflow run."""

    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    AWAITING_APPROVAL = auto()
    FAILED = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class TaskStatus(Enum):
    """Lifecycle status of a task assigned to an agent."""

    PENDING = auto()
    DISPATCHED = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELLED = auto()


class ReviewDecision(Enum):
    """Outcome of a review gate."""

    APPROVE = auto()
    REQUEST_CHANGES = auto()
    REJECT = auto()
    ABSTAIN = auto()


class ArtifactKind(Enum):
    """Classification of workflow artifacts."""

    DESIGN = auto()
    SOURCE = auto()
    TEST = auto()
    REVIEW = auto()
    LOG = auto()
    CONFIG = auto()
    OTHER = auto()


class RoleKind(Enum):
    """Well-known role kinds used in configuration.

    Free-form role names remain allowed in config; these enum values are the
    canonical kinds the engine and docs refer to.
    """

    ARCHITECTURE = auto()
    IMPLEMENTATION = auto()
    QUALITY_REVIEW = auto()
    REFACTORING = auto()
    TESTING = auto()
    DOCUMENTATION = auto()
    CUSTOM = auto()
