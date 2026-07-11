"""Domain identifiers and scalar value types.

Mechanics use Pydantic constraints and ``packaging.Version``. Domain behavior
(``is_compatible``, FieldPath structure) stays explicit on value objects.
"""

from __future__ import annotations

from functools import total_ordering
from typing import Annotated, Any, cast

from packaging.version import InvalidVersion, Version
from pydantic import Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import CoreSchema, core_schema

from domain.base import StringCoercibleVO

# ── syntax-only constrained strings (no behavior beyond validation) ─────

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

# Backward-compatible aliases (previously distinct RootModel subclasses).
DomainText = GovernanceText
GovernancePurpose = GovernanceText
GovernanceGuidance = GovernanceText
GovernanceConstraint = GovernanceText
GovernanceDescription = GovernanceText


def _parse_strict_semver(value: str) -> Version:
    """Parse MAJOR.MINOR.PATCH only (doctrine uses strict three-part versions)."""
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH")
    try:
        return Version(value)
    except InvalidVersion as exc:
        raise ValueError(f"Invalid semantic version {value!r}") from exc


@total_ordering
class SemanticVersion:
    """Semantic version with MAJOR compatibility for doctrine artifacts.

    Parsing and comparison are delegated to :class:`packaging.version.Version`.
    Domain rule ``is_compatible`` (same MAJOR) stays explicit here.
    """

    __slots__ = ("_version",)

    def __init__(self, value: str | Version | SemanticVersion) -> None:
        """Build from a three-part version string, packaging Version, or peer."""
        if isinstance(value, SemanticVersion):
            self._version = value._version
        elif isinstance(value, Version):
            # Re-validate strict three-part form via public string.
            self._version = _parse_strict_semver(
                f"{value.major}.{value.minor}.{value.micro}"
            )
        else:
            self._version = _parse_strict_semver(value)

    @classmethod
    def model_validate(cls, value: Any) -> SemanticVersion:
        """Pydantic-style entry point used by tests and call sites."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            data = cast(dict[str, Any], value)
            major = data.get("major")
            minor = data.get("minor")
            patch = data.get("patch", data.get("micro"))
            if major is None or minor is None or patch is None:
                raise ValueError(f"Invalid semantic version components: {value!r}")
            return cls(f"{major}.{minor}.{patch}")
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
        """PATCH version component (packaging ``micro``)."""
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
                result = self._version == _parse_strict_semver(other)
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
                [
                    core_schema.is_instance_schema(cls),
                    from_str,
                ]
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


class FieldPath(StringCoercibleVO):
    """Structured location of an identity field across layers.

    Has behavior (``is_field``, structured components) beyond bare string syntax.
    """

    collection: str = Field(min_length=1, description="Collection or container name")
    field: str = Field(min_length=1, description="Field name within the collection")
    raw: str = Field(min_length=1, description="Original path expression as authored")

    @classmethod
    def _parse_string(cls, value: str) -> dict[str, Any]:
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
        return {
            "collection": collection.strip(),
            "field": field.strip(),
            "raw": raw,
        }

    def __str__(self) -> str:
        return self.raw

    def is_field(self, name: str) -> bool:
        """Return True when this path ends at the given field name."""
        return self.field == name
