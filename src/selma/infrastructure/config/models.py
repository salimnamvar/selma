"""Configuration models — infrastructure config only.

Rule definitions live in schema/rules/*.json files (schema-driven).
This module contains ONLY infrastructure configuration (paths, output,
execution, tools, logging). Rule-specific config is in JSON rule files.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PathsConfig(BaseModel):
    """Directories and files to lint."""

    model_config = ConfigDict(frozen=True)

    include: tuple[str, ...] = ("src", "tests")
    exclude: tuple[str, ...] = (
        "__pycache__",
        "*.pyc",
        ".git",
        ".venv",
        "build",
        "dist",
        "*.egg-info",
    )
    extensions: tuple[str, ...] = (".py",)


class OutputConfig(BaseModel):
    """Output formatting options."""

    model_config = ConfigDict(frozen=True)

    format: str = "default"
    guide: bool = False
    file: str | None = None
    color: bool = True


class ExecutionConfig(BaseModel):
    """Execution behavior options."""

    model_config = ConfigDict(frozen=True)

    skip_tools: bool = False
    skip_ast: bool = False
    only: str | None = None
    max_workers: int = 4
    file_timeout: int = 30


class LoggingConfig(BaseModel):
    """Logging configuration."""

    model_config = ConfigDict(frozen=True)

    level: str = "WARNING"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str | None = None


class ToolConfig(BaseModel):
    """Configuration for an external tool (ruff, pylint, pyright)."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    binary: str = ""
    args: tuple[str, ...] = ()
    rcfile: str | None = None
    fail_under: int = 8


class RulesFilterConfig(BaseModel):
    """Top-level rule filtering by code."""

    model_config = ConfigDict(frozen=True)

    disabled: tuple[str, ...] = ("SC-031", "SC-033", "SC-065", "SC-092", "SC-114")
    codes: tuple[str, ...] = ()
    exclude_codes: tuple[str, ...] = ()


def _default_ruff() -> ToolConfig:
    return ToolConfig(binary="ruff")


def _default_pylint() -> ToolConfig:
    return ToolConfig(
        binary="pylint",
        rcfile="pylintrc",
        fail_under=8,
        args=("--recursive=y",),
    )


def _default_pyright() -> ToolConfig:
    return ToolConfig(binary="pyright", args=("--strict",))


class ToolsConfig(BaseModel):
    """External tools configuration."""

    model_config = ConfigDict(frozen=True)

    ruff: ToolConfig = Field(default_factory=_default_ruff)
    pylint: ToolConfig = Field(default_factory=_default_pylint)
    pyright: ToolConfig = Field(default_factory=_default_pyright)


class SelmaConfig(BaseModel):
    """Top-level immutable configuration.

    Rule definitions are NOT here — they live in schema/rules/*.json.
    This config controls infrastructure behavior only.
    """

    model_config = ConfigDict(frozen=True)

    version: str = "0.1.0"
    name: str = "selma"

    paths: PathsConfig = Field(default_factory=PathsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    rules_filter: RulesFilterConfig = Field(default_factory=RulesFilterConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
