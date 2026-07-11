from pydantic import Field

from domain.identifiers import WritingPrincipleId
from domain.value_objects.base import DomainValueObject


class WritingPrinciple(DomainValueObject):
    """A governance principle that guides rule authors in writing directives."""

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: str = Field(description="Short principle name")
    description: str = Field(description="Detailed guidance for applying this principle")
