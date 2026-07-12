"""Unit and contract tests for the PolicyDoctrine aggregate root."""

from __future__ import annotations

import pytest

from domain.policy_doctrine.contamination_guard import ContaminationGuard
from domain.policy_doctrine.cross_layer_binding import (
    ConflictResolutionBinding,
    CrossLayerBinding,
    FieldLegality,
)
from domain.policy_doctrine.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.policy_doctrine.lifecycle_definition import LifecycleDefinition
from domain.policy_doctrine.policy_doctrine import PolicyDoctrine as PolicyDoctrineClass
from domain.policy_doctrine.priority_hierarchy import CrossLayerPrecedence, Level, PriorityHierarchy
from domain.policy_doctrine.sections import Section as SectionModel
from domain.policy_doctrine.version_strategy import SemanticVersion, VersionStrategy
from domain.policy_doctrine.writing_principles import WritingPrinciple


@pytest.mark.unit
@pytest.mark.domain
class TestPolicyDoctrineModel:
    """PolicyDoctrine aggregate root model invariants."""

    def test_model_has_no_field_aliases(self) -> None:
        models = (
            PolicyDoctrineClass,
            CrossLayerBinding,
            ConflictResolutionBinding,
            FieldLegality,
            IdentityResolution,
            MachineIdSemantics,
            LifecycleDefinition,
            ContaminationGuard,
            PriorityHierarchy,
            Level,
            CrossLayerPrecedence,
            VersionStrategy,
            SemanticVersion,
            WritingPrinciple,
            SectionModel,
        )
        aliases = [
            f"{model.__name__}.{name}={field.alias}"
            for model in models
            for name, field in model.model_fields.items()
            if field.alias is not None and field.alias != name
        ]
        assert aliases == []
