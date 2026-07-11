from typing import List

from pydantic import BaseModel, Field

from domain.enums import ProhibitedField


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = {"frozen": True}

    prohibited_fields: List[ProhibitedField] = Field(description="Schema fields that must not appear in policy prose")
    allowed_machine_references: List[str] = Field(description="How Machine IDs may appear in policy")
    metadata_note: str = Field(description="Constraints on schema metadata in policy")
