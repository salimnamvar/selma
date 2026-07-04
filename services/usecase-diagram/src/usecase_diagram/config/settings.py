"""Pydantic settings for the usecase-diagram subproject."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

_AGENT_GLOBAL = Path.home() / ".agent-global" / "shared"


class UseCaseDiagramConfig(BaseSettings):
    """Application configuration — reads from environment and .env files."""

    model_config = {"env_prefix": "UD_", "env_file": ".env", "env_file_encoding": "utf-8"}

    rules_dir: Path = Field(
        default=_AGENT_GLOBAL / "rules" / "software-design" / "usecase-diagram",
        description="Directory containing rule contracts (YAML).",
    )
    templates_dir: Path = Field(
        default=_AGENT_GLOBAL / "templates",
        description="Directory containing document templates.",
    )
    shared_dir: Path = Field(
        default=_AGENT_GLOBAL,
        description="Root of the shared knowledge directory.",
    )
    contracts_dir: Path | None = Field(
        default=None,
        description="Override for contracts subdirectory (defaults to rules_dir/contracts).",
    )
    log_level: str = Field(default="INFO", description="Logging level.")

    @field_validator("rules_dir", "templates_dir", "shared_dir", mode="before")
    @classmethod
    def _expand_home(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()

    @field_validator("contracts_dir", mode="before")
    @classmethod
    def _resolve_contracts(cls, v: str | Path | None) -> Path | None:
        if v is None:
            return None
        return Path(v).expanduser().resolve()

    @property
    def resolved_contracts_dir(self) -> Path:
        """Return the contracts directory, falling back to rules_dir/contracts."""
        if self.contracts_dir is not None:
            return self.contracts_dir
        return self.rules_dir / "contracts"


@lru_cache(maxsize=1)
def get_config() -> UseCaseDiagramConfig:
    """Singleton accessor for the application configuration."""
    return UseCaseDiagramConfig()
