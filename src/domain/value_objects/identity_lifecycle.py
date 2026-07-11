from pydantic import BaseModel, ConfigDict, Field

from domain.enums import IdentityOperation
from domain.identifiers import Prose


class LifecycleOperationIntent(BaseModel):
    """Describes the governance intent for a specific identity lifecycle operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: IdentityOperation = Field(description="The lifecycle operation")
    intent: Prose = Field(description="Governance intent for this operation")


class IdentityLifecycleIntent(BaseModel):
    """Describes governance intent for all identity lifecycle operations.

    Uses a collection of LifecycleOperationIntent to satisfy the Open-Closed Principle:
    new operations can be added without modifying this class.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    operations: tuple[LifecycleOperationIntent, ...] = Field(description="Operation-specific intents")
    dag_intent: Prose = Field(description="Constraint on lineage ancestry graph structure")
