from pydantic import BaseModel, ConfigDict, Field


class TableColumn(BaseModel):
    """Value object representing a column in a governance table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Column name")
    required: bool = Field(default=True, description="Whether this column is required")
    description: str = Field(description="Column purpose and content")
