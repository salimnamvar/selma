"""Finding output model for Selma."""

from enum import StrEnum

from pydantic import BaseModel

class Weight(StrEnum):
    """Severity weight for findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Finding(BaseModel):
    """A lint finding produced by rule evaluation."""

    rule_id: str
    file: str
    line: int
    message: str
    weight: Weight
