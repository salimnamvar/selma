from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class IdentityLifecycleIntent(BaseModel):
    """Describes when to use each identity lifecycle operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: Guidance = Field(description="When to use revision")
    fork: Guidance = Field(description="When to use fork")
    merge: Guidance = Field(description="When to use merge")
    split: Guidance = Field(description="When to use split")
    rename: Guidance = Field(description="When to use rename")
    retire: Guidance = Field(description="When to use retire")
    dag_intent: Guidance = Field(description="Constraint on lineage ancestry graph structure")
