from typing import Annotated

from pydantic import Field

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

SemanticVersion = Annotated[
    str,
    Field(pattern=r"^\d+\.\d+\.\d+$", description="Semantic version in MAJOR.MINOR.PATCH format"),
]

SectionId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier"),
]

Guidance = Annotated[
    str,
    Field(min_length=1, description="Governance guidance or policy prose"),
]

Description = Annotated[
    str,
    Field(min_length=1, description="Human-readable description"),
]
