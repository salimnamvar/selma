"""Domain identifiers — constrained strings + packaging-backed SemanticVersion."""

from __future__ import annotations

from functools import total_ordering
from typing import Annotated, Any

from packaging.version import InvalidVersion, Version
from pydantic import Field, GetCoreSchemaHandler, GetJsonSchemaHandler, model_validator
from pydantic_core import CoreSchema, core_schema

from domain.base import DomainValueObject

GovernanceText = Annotated[
    str,
    Field(min_length=1, description="Non-empty governance guidance, description, or intent"),
]

MachineId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable lineage identifier assigned at directive authoring time",
    ),
]

WritingPrincipleId = Annotated[
    str,
    Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier"),
]

SectionId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier"),
]

RuleContractId = Annotated[
    str,
    Field(
        pattern=r"^[a-z][a-z0-9-]*$",
        min_length=1,
        description="Identifier of the compatible rule schema",
    ),
]


def _parse_semver(value: str) -> Version:
    """Parse strict MAJOR.MINOR.PATCH via packaging."""
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH")
    try:
        result = Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"Invalid semantic version {value!r}") from exc
    return result


@total_ordering
class SemanticVersion:
    """Three-component semantic version delegated to packaging.Version."""

    __slots__ = ("_version",)

    def __init__(self, value: str | Version | SemanticVersion) -> None:
        """Build from a three-part version string, packaging Version, or peer."""
        if isinstance(value, SemanticVersion):
            self._version = value._version
        elif isinstance(value, Version):
            self._version = _parse_semver(f"{value.major}.{value.minor}.{value.micro}")
        else:
            self._version = _parse_semver(value)

    @classmethod
    def model_validate(cls, value: Any) -> SemanticVersion:
        """Validate from string, packaging Version, or peer instance."""
        if isinstance(value, cls):
            return value
        if isinstance(value, (str, Version)):
            return cls(value)
        raise TypeError(f"Cannot validate SemanticVersion from {type(value)!r}")

    @property
    def major(self) -> int:
        """MAJOR version component."""
        return int(self._version.major)

    @property
    def minor(self) -> int:
        """MINOR version component."""
        return int(self._version.minor)

    @property
    def patch(self) -> int:
        """PATCH version component (packaging micro)."""
        return int(self._version.micro)

    def is_compatible(self, other: SemanticVersion) -> bool:
        """Return True when both versions share the same MAJOR component."""
        return self.major == other.major

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SemanticVersion({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        result: Any = NotImplemented
        if isinstance(other, SemanticVersion):
            result = self._version == other._version
        elif isinstance(other, str):
            try:
                result = self._version == _parse_semver(other)
            except ValueError:
                result = False
        return result

    def __hash__(self) -> int:
        return hash(self._version)

    def __lt__(self, other: object) -> bool:
        result: Any = NotImplemented
        if isinstance(other, SemanticVersion):
            result = self._version < other._version
        return result

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source: type[Any],
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def validate(value: Any) -> SemanticVersion:
            return cls.model_validate(value)

        from_str = core_schema.no_info_plain_validator_function(validate)
        return core_schema.json_or_python_schema(
            json_schema=from_str,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(cls), from_str]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance),
                when_used="always",
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> dict[str, Any]:
        return handler(core_schema.str_schema())


class FieldPath(DomainValueObject):
    """Structured location of an identity field (string-coercible)."""

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @model_validator(mode="before")
    @classmethod
    def _parse_string(cls, value: Any) -> Any:
        result: Any = value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("Field path must be non-empty")
            collection: str
            field: str
            if "[]." in raw:
                collection, field = raw.rsplit("[].", maxsplit=1)
            elif "." in raw:
                collection, field = raw.rsplit(".", maxsplit=1)
            else:
                collection, field = raw, raw
            result = {
                "collection": collection.strip(),
                "field": field.strip(),
                "raw": raw,
            }
        return result

    def __str__(self) -> str:
        return self.raw

    def is_field(self, name: str) -> bool:
        """Return True when this path ends at the given field name."""
        return self.field == name
