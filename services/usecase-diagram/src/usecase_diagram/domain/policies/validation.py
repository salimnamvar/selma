"""Validation policy — orchestrates check execution against diagrams and projects."""

from __future__ import annotations

from usecase_diagram.domain.entities.contract import ContractBundle
from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import AssessmentResult, Violation


class ValidationPolicy:
    """Interface for validation execution — implemented by the service layer."""

    def validate_diagram(
        self, diagram: UCDiagram, bundle: ContractBundle
    ) -> list[Violation]:
        raise NotImplementedError

    def validate_project(
        self,
        diagrams: list[UCDiagram],
        bundle: ContractBundle,
        project_context: dict | None = None,
    ) -> list[Violation]:
        raise NotImplementedError

    def run_assessments(
        self,
        diagrams: list[UCDiagram],
        bundle: ContractBundle,
        project_context: dict | None = None,
    ) -> list[AssessmentResult]:
        raise NotImplementedError
