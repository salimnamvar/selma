from typing import Annotated, Any

from pydantic import Field, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

import re


class SemanticVersion:
    """Rich value object for semantic versioning."""

    def __init__(self, major: int, minor: int, patch: int) -> None:
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def _validate(cls, v: Any) -> "SemanticVersion":
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            parts = v.split(".")
            if len(parts) != 3:
                raise ValueError("Semantic version must be in MAJOR.MINOR.PATCH format")
            try:
                return cls(int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                raise ValueError("Semantic version components must be integers")
        raise ValueError("Invalid semantic version")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SemanticVersion):
            return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
        return False

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))

    def __lt__(self, other: "SemanticVersion") -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "SemanticVersion") -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: "SemanticVersion") -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "SemanticVersion") -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """Two versions are compatible iff they share the same MAJOR version."""
        return self.major == other.major


class MachineId:
    """Rich value object for machine identity."""

    _pattern = re.compile(r"^([A-Z][A-Z0-9]+)-([0-9]+)$")

    def __init__(self, value: str) -> None:
        match = self._pattern.match(value)
        if not match:
            raise ValueError(f"Invalid Machine ID format: {value}")
        self.value = value
        self.prefix = match.group(1)
        self.number = int(match.group(2))

    @classmethod
    def _validate(cls, v: Any) -> "MachineId":
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            return cls(v)
        raise ValueError("Machine ID must be a string")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(
            cls._validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MachineId) and self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


SectionId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier")]

WritingPrincipleId = Annotated[str, Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier")]

RuleContractId = Annotated[str, Field(min_length=1, description="Rule contract identifier")]

FieldPath = Annotated[str, Field(min_length=1, description="Dotted path to a field in a layer")]

Prose = Annotated[str, Field(min_length=1, description="Governance prose or guidance")]
