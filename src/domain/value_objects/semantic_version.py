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

    def _tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __lt__(self, other: "SemanticVersion") -> bool:
        return self._tuple() < other._tuple()

    def __le__(self, other: "SemanticVersion") -> bool:
        return self._tuple() <= other._tuple()

    def __gt__(self, other: "SemanticVersion") -> bool:
        return self._tuple() > other._tuple()

    def __ge__(self, other: "SemanticVersion") -> bool:
        return self._tuple() >= other._tuple()

    def __str__(self) -> str:
        return self.value
