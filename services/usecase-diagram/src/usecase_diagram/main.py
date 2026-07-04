"""Application factory for the usecase-diagram subproject."""

from __future__ import annotations

from usecase_diagram.config.settings import UseCaseDiagramConfig, get_config
from usecase_diagram.repository.contracts import ContractRepository
from usecase_diagram.repository.diagrams import DiagramRepository
from usecase_diagram.repository.project import ProjectRepository
from usecase_diagram.service.fixing import FixingService
from usecase_diagram.service.validation import ValidationService


class UseCaseDiagramApplication:
    """Composition root — wires all layers together."""

    def __init__(self, config: UseCaseDiagramConfig | None = None) -> None:
        self._config = config or get_config()
        self._contract_repo = ContractRepository(self._config.resolved_contracts_dir)
        self._diagram_repo = DiagramRepository()
        self._validation_svc = ValidationService(self._contract_repo)
        self._fixing_svc = FixingService(self._diagram_repo)

    @property
    def config(self) -> UseCaseDiagramConfig:
        return self._config

    @property
    def contract_repo(self) -> ContractRepository:
        return self._contract_repo

    @property
    def diagram_repo(self) -> DiagramRepository:
        return self._diagram_repo

    @property
    def validation_svc(self) -> ValidationService:
        return self._validation_svc

    @property
    def fixing_svc(self) -> FixingService:
        return self._fixing_svc

    def project_repo(self, project_root: str) -> ProjectRepository:
        return ProjectRepository(project_root)
