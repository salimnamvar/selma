from pydantic import Field

from domain.value_objects.base import DomainValueObject


class MachineId(DomainValueObject):
    """Immutable lineage identifier assigned at directive authoring time.

    Centralizes governance semantics for the canonical identity root.
    """

    value: str = Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable lineage identifier assigned at directive authoring time",
    )

    def __str__(self) -> str:
        return self.value
