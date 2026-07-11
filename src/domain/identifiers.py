from typing import Annotated

from pydantic import Field

WritingPrincipleId = Annotated[
    str,
    Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier"),
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
