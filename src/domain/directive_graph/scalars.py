"""Scalar types for the Directive Graph bounded context.

Pattern-only scalars are ``Annotated`` type aliases — no class overhead.
Behaviour-bearing scalars use ``RootModel[str]`` to expose property methods.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.5
"""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import ConfigDict
from pydantic import Field
from pydantic import RootModel
from pydantic.functional_validators import AfterValidator

# ---------------------------------------------------------------------------
# Internal validators
# ---------------------------------------------------------------------------


def _require_finite(value: float) -> float:
    """Reject NaN and ±Infinity; return the value unchanged if finite."""
    if not math.isfinite(value):
        raise ValueError(f"value must be a finite IEEE 754 number; got {value!r}")
    return value


# ---------------------------------------------------------------------------
# Pattern-only scalars — Annotated[str, Field(...)]
# ---------------------------------------------------------------------------

LineageId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable root identifier. Assigned once, never reused.",
    ),
]
"""Immutable root identity of a directive (e.g. ``RULE-001``)."""

ExecutionId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$",
        description="Active execution identifier. May change on fork/merge/split.",
    ),
]
"""Mutable execution identity of a directive (e.g. ``RULE-001-A``)."""

# Semantic alias — same pattern as ExecutionId but communicates cross-directive reference.
DirectiveReference = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$",
        description="Reference to another directive by its execution ID.",
    ),
]
"""Typed reference to another directive by ExecutionId."""

UtcTimestamp = Annotated[
    str,
    Field(
        pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$",
        description="ISO 8601 UTC timestamp. Z suffix required; offsets (±HH:MM) are rejected.",
    ),
]
"""ISO 8601 UTC timestamp. Lexicographically comparable for ordering."""

RegexPattern = Annotated[
    str,
    Field(
        min_length=1,
        max_length=4096,
        description="Regex pattern string. RE2 compatibility enforced at compile time.",
    ),
]
"""RE2-compatible regex pattern (length 1–4096). RE2 linting is infrastructure."""

RegexFlags = Annotated[
    str,
    Field(
        pattern=r"^[ims]*$",
        description="Regex flags; any combination of i, m, s.",
    ),
]
"""Regex modifier flags. Empty string means no flags."""

AnchorReference = Annotated[
    str,
    Field(
        pattern=r"^(section:[a-z][a-z_]*(/[a-z_]+)?|/.+)$",
        description="Link to policy document section or JSON Pointer (RFC 6901).",
    ),
]
"""Traceable link to a policy document section or JSON Pointer."""

PolicyContractId = Annotated[
    str,
    Field(
        pattern=r"^universal-policy-doctrine$",
        description="Constant identifier of the paired policy contract.",
    ),
]
"""Constant policy contract identifier: ``"universal-policy-doctrine"``."""

ActorId = Annotated[
    str,
    Field(min_length=1, description="Non-empty identifier of an authenticated actor."),
]
"""Non-empty actor identifier (used for authorship and approval)."""

FiniteFloat = Annotated[
    float,
    AfterValidator(_require_finite),
    Field(description="Finite IEEE 754 double. NaN and ±Infinity are rejected."),
]
"""IEEE 754 finite double — NaN and ±Infinity are not permitted."""


# ---------------------------------------------------------------------------
# Behaviour-bearing scalar — RootModel[str]
# ---------------------------------------------------------------------------


class SemanticVersion(RootModel[str]):
    """Semantic version string with component access (MAJOR.MINOR.PATCH).

    Attributes:
        root (str): Raw version string matching ``^\\d+\\.\\d+\\.\\d+$``.
    """

    root: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version string (MAJOR.MINOR.PATCH).",
    )
    model_config = ConfigDict(frozen=True)

    @property
    def major(self) -> int:
        """MAJOR version component.

        Returns:
            int: Major version number.
        """
        return int(self.root.split(".")[0])

    @property
    def minor(self) -> int:
        """MINOR version component.

        Returns:
            int: Minor version number.
        """
        return int(self.root.split(".")[1])

    @property
    def patch(self) -> int:
        """PATCH version component.

        Returns:
            int: Patch version number.
        """
        return int(self.root.split(".")[2])

    def is_major_compatible(self, other: SemanticVersion) -> bool:
        """Return True iff both versions share the same MAJOR.

        Args:
            other (SemanticVersion): Version to compare against.

        Returns:
            bool: True when major versions are equal.
        """
        return self.major == other.major

    def __str__(self) -> str:
        return self.root
