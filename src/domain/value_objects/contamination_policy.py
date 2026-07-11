from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField
from domain.identifiers import Prose


class ContaminationPolicy(BaseModel):
    """Defines what is prohibited in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: frozenset[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[Prose, ...] = Field(description="How Machine IDs may appear in policy")
    metadata_note: Prose = Field(description="Constraints on schema metadata in policy")
