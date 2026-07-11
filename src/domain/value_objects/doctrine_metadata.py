from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Prose, RuleContractId, SemanticVersion


class RuleContractReference(BaseModel):
    """Reference to the compatible rule contract."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: RuleContractId = Field(description="Rule contract identifier")
    version: SemanticVersion = Field(description="Compatible rule contract version")


class DoctrineMetadata(BaseModel):
    """Identity and versioning metadata for the doctrine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: Prose = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    contract: RuleContractReference = Field(description="Compatible rule contract reference")
