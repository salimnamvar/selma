from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField


class ProhibitedFieldSet(BaseModel):
    """Value object wrapping a set of prohibited fields with domain methods."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    fields: frozenset[ProhibitedField] = Field(description="Set of prohibited schema fields")

    def contains(self, field_name: str) -> bool:
        """Check if a field name is in the prohibited set."""
        try:
            field = ProhibitedField(field_name)
            return field in self.fields
        except ValueError:
            return False

    def __len__(self) -> int:
        return len(self.fields)

    def __iter__(self):  # type: ignore[override]
        return iter(self.fields)
