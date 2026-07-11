from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects.contamination_policy import ContaminationPolicy
from domain.value_objects.cross_layer_policy import CrossLayerPolicy


class GovernanceConstraints(BaseModel):
    """Clustered governance constraints for the doctrine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contamination: ContaminationPolicy = Field(description="Policy-layer field constraints")
    cross_layer: CrossLayerPolicy = Field(description="Cross-layer relationship constraints")
