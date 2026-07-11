from typing import Dict

from pydantic import BaseModel, Field

from domain.enums import IdentityOperation


class IdentityLifecycleIntent(BaseModel):
    """Describes when to use each identity lifecycle operation."""

    model_config = {"frozen": True}

    intents: Dict[IdentityOperation, str] = Field(description="Mapping of operation to governance intent")
    dag_intent: str = Field(description="Constraint on lineage ancestry graph structure")
