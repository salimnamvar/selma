"""Pydantic settings for the usecase-diagram subproject."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class UseCaseDiagramConfig(BaseSettings):
    """Application configuration — reads from environment and .env files.

    Attributes:
        rules_dir (Path): Directory containing rule files.
        templates_dir (Path): Directory containing document templates.
        shared_dir (Path): Root of the shared knowledge directory.
        rules_file (Optional[Path]): Override for rules YAML file.
        log_level (str): Logging level.
    """

    model_config = {"env_prefix": "UD_", "env_file": ".env", "env_file_encoding": "utf-8"}

    rules_dir: Path = Field(
        default=Path.home() / ".agent-global" / "shared" / "rules" / "selma" / "usecase-diagram",
        description="Directory containing rule files.",
    )
    templates_dir: Path = Field(
        default=Path.home() / ".agent-global" / "shared" / "templates",
        description="Directory containing document templates.",
    )
    shared_dir: Path = Field(
        default=Path.home() / ".agent-global" / "shared",
        description="Root of the shared knowledge directory.",
    )
    rules_file: Optional[Path] = Field(
        default=None,
        description="Override for rules YAML file (defaults to rules_dir/rule.yaml).",
    )
    log_level: str = Field(default="INFO", description="Logging level.")

    @field_validator("rules_dir", "templates_dir", "shared_dir", mode="before")
    @classmethod
    def _expand_home(cls, a_value: Union[str, Path]) -> Path:
        """Expand user home and resolve path.

        Args:
            a_value (Union[str, Path]): Path to expand.

        Returns:
            Path: Resolved absolute path.
        """
        result: Path = Path(a_value).expanduser().resolve()
        return result

    @field_validator("rules_file", mode="before")
    @classmethod
    def _resolve_rules_file(cls, a_value: Union[str, Path, None]) -> Optional[Path]:
        """Resolve rules file path if provided.

        Args:
            a_value (Union[str, Path, None]): Path or None.

        Returns:
            Optional[Path]: Resolved path or None.
        """
        result: Optional[Path] = None
        if a_value is not None:
            result = Path(a_value).expanduser().resolve()
        return result

    @property
    def resolved_rules_file(self) -> Path:
        """Return the rules file, falling back to rules_dir/rule.yaml.

        Returns:
            Path: Resolved rules file path.
        """
        result: Path
        if self.rules_file is not None:
            result = self.rules_file
        else:
            result = self.rules_dir / "rule.yaml"
        return result


@lru_cache(maxsize=1)
def get_config() -> UseCaseDiagramConfig:
    """Return the singleton application configuration.

    Returns:
        UseCaseDiagramConfig: Cached configuration instance.
    """
    result: UseCaseDiagramConfig = UseCaseDiagramConfig()
    return result
