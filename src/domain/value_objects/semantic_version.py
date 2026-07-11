from pydantic import Field

from domain.value_objects.base import DomainValueObject


class SemanticVersion(DomainValueObject):
    """Semantic version capturing the core governance rule: compatibility = same MAJOR version."""

    value: str = Field(pattern=r"^\d+\.\d+\.\d+$", description="Semantic version in MAJOR.MINOR.PATCH format")

    @property
    def major(self) -> int:
        return int(self.value.split(".")[0])

    @property
    def minor(self) -> int:
        return int(self.value.split(".")[1])

    @property
    def patch(self) -> int:
        return int(self.value.split(".")[2])

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """Two versions are compatible iff they share the same MAJOR version."""
        return self.major == other.major

    def __str__(self) -> str:
        return self.value
