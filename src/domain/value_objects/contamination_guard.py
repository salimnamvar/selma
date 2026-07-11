from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: frozenset[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[str, ...] = Field(description="How Machine IDs may appear in policy")
    metadata_note: str = Field(description="Constraints on schema metadata in policy")
