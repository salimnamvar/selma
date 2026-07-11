"""Doctrine — identity and version metadata (policy_doctrine.yaml: doctrine)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.base import VO_CONFIG
from domain.identifiers import GovernanceText, SchemaId, SemanticVersion


class Doctrine(BaseModel):
    """Identity and compatibility metadata for a policy doctrine document."""

    model_config = VO_CONFIG

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: GovernanceText = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: SchemaId = Field(description="Identifier of the compatible rule schema")

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when doctrine MAJOR matches both artifact versions."""
        return self.version.is_compatible(spec_version) and self.version.is_compatible(schema_version)