from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Prose
from domain.value_objects.prohibited_field_set import ProhibitedFieldSet


class ContaminationPolicy(BaseModel):
    """Defines what is prohibited in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: ProhibitedFieldSet = Field(description="Schema fields that must not appear in policy prose")
    allowed_machine_references: tuple[Prose, ...] = Field(description="How Machine IDs may appear in policy")
    metadata_note: Prose = Field(description="Constraints on schema metadata in policy")
