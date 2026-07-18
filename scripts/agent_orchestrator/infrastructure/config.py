"""Application settings skeleton (Pydantic Settings).

Foundation scope: define configuration shape and file path conventions only.
YAML loading into domain models is a later repository-layer task.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """Runtime settings for the orchestrator CLI and services.

    Environment prefix: ``AO_`` (Agent Orchestrator).

    Attributes:
        config_dir: Directory containing agents/workflows/roles YAML.
        workspace_path: Default workspace for agent execution.
        artifacts_dir: Directory for run artifacts (relative to workspace if not absolute).
        state_dir: Directory for persisted workflow state.
        log_level: Logging level name.
    """

    model_config = SettingsConfigDict(env_prefix="AO_")

    config_dir: Path = Field(
        default=Path("config"),
        description="Directory with agents.yaml, workflow.yaml, roles.yaml, prompts.yaml",
    )
    workspace_path: Path = Field(
        default=Path(),
        description="Default workspace root for agent execution",
    )
    artifacts_dir: Path = Field(
        default=Path(".orchestrator/artifacts"),
        description="Artifact storage root",
    )
    state_dir: Path = Field(
        default=Path(".orchestrator/state"),
        description="Workflow run state storage root",
    )
    log_level: str = Field(default="INFO", description="Logging level")

    def agents_config_path(self) -> Path:
        """Path to agents configuration file.

        Returns:
            ``config_dir / agents.yaml``.
        """
        return self.config_dir / "agents.yaml"

    def workflow_config_path(self) -> Path:
        """Path to workflow configuration file.

        Returns:
            ``config_dir / workflow.yaml``.
        """
        return self.config_dir / "workflow.yaml"

    def roles_config_path(self) -> Path:
        """Path to roles configuration file.

        Returns:
            ``config_dir / roles.yaml``.
        """
        return self.config_dir / "roles.yaml"

    def prompts_config_path(self) -> Path:
        """Path to prompts configuration file.

        Returns:
            ``config_dir / prompts.yaml``.
        """
        return self.config_dir / "prompts.yaml"
