"""Application factory for the usecase-diagram subproject."""

from __future__ import annotations

from typing import Optional

from usecase_diagram.config.settings import UseCaseDiagramConfig, get_config
from usecase_diagram.repository.contracts import ContractRepository
from usecase_diagram.repository.diagrams import DiagramRepository
from usecase_diagram.repository.project import ProjectRepository
from usecase_diagram.service.fixing import FixingService
from usecase_diagram.service.validation import ValidationService


class UseCaseDiagramApplication:
    """Composition root — wires all layers together.

    Attributes:
        _config (UseCaseDiagramConfig): Application configuration.
        _contract_repo (ContractRepository): Contract data access.
        _diagram_repo (DiagramRepository): Diagram data access.
        _validation_svc (ValidationService): Validation orchestration.
        _fixing_svc (FixingService): Fixing orchestration.
    """

    def __init__(self, a_config: Optional[UseCaseDiagramConfig] = None) -> None:
        """Initialize the application with optional config override.

        Args:
            a_config (Optional[UseCaseDiagramConfig]): Config or None for default.
        """
        self._config: UseCaseDiagramConfig = a_config or get_config()
        self._contract_repo: ContractRepository = ContractRepository(
            self._config.resolved_contracts_dir
        )
        self._diagram_repo: DiagramRepository = DiagramRepository()
        self._validation_svc: ValidationService = ValidationService(self._contract_repo)
        self._fixing_svc: FixingService = FixingService(self._diagram_repo)

    @property
    def config(self) -> UseCaseDiagramConfig:
        """Application configuration."""
        return self._config

    @property
    def contract_repo(self) -> ContractRepository:
        """Contract data access repository."""
        return self._contract_repo

    @property
    def diagram_repo(self) -> DiagramRepository:
        """Diagram data access repository."""
        return self._diagram_repo

    @property
    def validation_svc(self) -> ValidationService:
        """Validation orchestration service."""
        return self._validation_svc

    @property
    def fixing_svc(self) -> FixingService:
        """Fixing orchestration service."""
        return self._fixing_svc

    def project_repo(self, a_project_root: str) -> ProjectRepository:
        """Create a project repository for the given root.

        Args:
            a_project_root (str): Path to the project root directory.

        Returns:
            ProjectRepository: Configured project repository.
        """
        result: ProjectRepository = ProjectRepository(a_project_root)
        return result
