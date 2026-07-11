from pydantic import BaseModel, Field

from domain.identifiers import SemanticVersion


class DoctrineMetadata(BaseModel):
    """Identifying metadata for the policy doctrine and its compatible schema versions."""

    model_config = {"frozen": True}

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: str = Field(description="Identifier of the compatible rule schema")
