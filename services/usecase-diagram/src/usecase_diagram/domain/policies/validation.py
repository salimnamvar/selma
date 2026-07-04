"""Validation policy — orchestrates check execution against diagrams and projects."""

from __future__ import annotations

from typing import List, Optional

from usecase_diagram.domain.entities.contract import ContractBundle
from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import AssessmentResult, Violation


class ValidationPolicy:
    """Interface for validation execution — implemented by the service layer.

    Subclasses must implement all abstract methods.
    """

    def validate_diagram(
        self,
        a_diagram: UCDiagram,
        a_bundle: ContractBundle,
    ) -> List[Violation]:
        """Validate a single diagram against all applicable rules.

        Args:
            a_diagram (UCDiagram): Diagram to validate.
            a_bundle (ContractBundle): Contract bundle.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        Returns:
            List[Violation]: List of violations found.
        """
        raise NotImplementedError

    def validate_project(
        self,
        a_diagrams: List[UCDiagram],
        a_bundle: ContractBundle,
        a_project_context: Optional[dict] = None,
    ) -> List[Violation]:
        """Validate all diagrams at project level.

        Args:
            a_diagrams (List[UCDiagram]): List of diagrams to validate.
            a_bundle (ContractBundle): Contract bundle.
            a_project_context (Optional[dict]): Project context.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        Returns:
            List[Violation]: List of violations found.
        """
        raise NotImplementedError

    def run_assessments(
        self,
        a_diagrams: List[UCDiagram],
        a_bundle: ContractBundle,
        a_project_context: Optional[dict] = None,
    ) -> List[AssessmentResult]:
        """Run principle assessments against the project.

        Args:
            a_diagrams (List[UCDiagram]): List of diagrams.
            a_bundle (ContractBundle): Contract bundle.
            a_project_context (Optional[dict]): Project context.

        Raises:
            NotImplementedError: Must be implemented by subclass.

        Returns:
            List[AssessmentResult]: Assessment results.
        """
        raise NotImplementedError
