from pydantic import BaseModel, ConfigDict, Field


class IdentityLifecycleIntent(BaseModel):
    """Describes when to use each identity lifecycle operation.

    Each field corresponds to one operation in the lineage identity lifecycle.
    The set of operations is closed and fixed by the governance framework.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: str = Field(description="When to use revision")
    fork: str = Field(description="When to use fork")
    merge: str = Field(description="When to use merge")
    split: str = Field(description="When to use split")
    rename: str = Field(description="When to use rename")
    retire: str = Field(description="When to use retire")
    dag_intent: str = Field(description="Constraint on lineage ancestry graph structure")
