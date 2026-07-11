"""Policy doctrine value objects."""

from __future__ import annotations

from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import (
    ConflictResolutionIntent,
    CrossLayerBinding,
    FieldLegality,
)
from domain.value_objects.document_section import (
    DIRECTIVES_CHILD_IDS,
    REQUIRED_SECTION_IDS,
    DocumentSection,
    DocumentTemplate,
)
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.lifecycle_guidance import LifecycleGuidance
from domain.value_objects.priority_hierarchy import (
    AuthorityHierarchy,
    CrossLayerPrecedence,
    PriorityLevel,
)
from domain.value_objects.versioning_intent import VersionComponentIntent, VersioningIntent
from domain.value_objects.writing_principle import WritingPrinciple, WritingPrinciples

__all__ = [
    "DIRECTIVES_CHILD_IDS",
    "REQUIRED_SECTION_IDS",
    "AuthorityHierarchy",
    "ConflictResolutionIntent",
    "ContaminationGuard",
    "CrossLayerBinding",
    "CrossLayerPrecedence",
    "DocumentSection",
    "DocumentTemplate",
    "FieldLegality",
    "IdentityResolution",
    "LifecycleGuidance",
    "MachineIdSemantics",
    "PriorityLevel",
    "VersionComponentIntent",
    "VersioningIntent",
    "WritingPrinciple",
    "WritingPrinciples",
]