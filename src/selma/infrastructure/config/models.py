"""Configuration models — infrastructure config only.

Rule definitions live in directive/rule/*.json files (schema-driven).
Policy definitions live in directive/policy/*.yaml files.
Schema definitions live in schema/*.json and schema/*.yaml files.

ALL values MUST be configured externally via:
- pyproject.toml [tool.selma] sections
- Environment variables SELMA_*
- CLI arguments

No defaults, no hardcoded paths, no hardcoded patterns in source.
Every field is required unless explicitly marked Optional (nullable).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class DirectivePathsConfig(BaseModel):
    """Paths to directive directories (policy and rule definitions).

    Required. Configure via SELMA_DIRECTIVE_* env vars,
    [tool.selma.directive] in pyproject.toml, or CLI args.
    """

    model_config = ConfigDict(frozen=True)

    root: Path = Field(description="Root directive directory")
    policy_dir: Path = Field(description="Policy definitions directory")
    rule_dir: Path = Field(description="Rule definitions directory")


class SchemaPathsConfig(BaseModel):
    """Paths to schema definitions (rule schema, policy doctrine).

    Required. Configure via SELMA_SCHEMA_* env vars,
    [tool.selma.schema] in pyproject.toml, or CLI args.
    """

    model_config = ConfigDict(frozen=True)

    root: Path = Field(description="Root schema directory")
    rule_schema: Path = Field(description="Rule schema JSON file")
    policy_doctrine: Path = Field(description="Policy doctrine YAML file")


class PathsConfig(BaseModel):
    """Directories and files to lint.

    Required. Configure via [tool.selma.paths] in pyproject.toml
    or SELMA_PATHS_* env vars.
    """

    model_config = ConfigDict(frozen=True)

    include: tuple[str, ...] = Field(description="Directories/files to lint")
    exclude: tuple[str, ...] = Field(description="Patterns to exclude from linting")
    extensions: tuple[str, ...] = Field(description="File extensions to lint")


class OutputConfig(BaseModel):
    """Output formatting options.

    Required. Configure via [tool.selma.output] in pyproject.toml
    or SELMA_OUTPUT_* env vars.
    """

    model_config = ConfigDict(frozen=True)

    format: str = Field(description="Output format: default, json, gcc, guidance")
    guide: bool = Field(description="Include guidance in output")
    file: str | None = Field(description="Output file path (stdout if None)")
    color: bool = Field(description="Enable colored output")


class ExecutionConfig(BaseModel):
    """Execution behavior options.

    Required. Configure via [tool.selma.execution] in pyproject.toml
    or SELMA_EXECUTION_* env vars.
    """

    model_config = ConfigDict(frozen=True)

    skip_tools: bool = Field(description="Skip external tools")
    skip_ast: bool = Field(description="Skip AST rules")
    only: str | None = Field(description="Run only one check")
    max_workers: int = Field(description="Maximum parallel workers")
    file_timeout: int = Field(description="Per-file timeout in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration.

    Required. Configure via [tool.selma.logging] in pyproject.toml
    or SELMA_LOGGING_* env vars.
    """

    model_config = ConfigDict(frozen=True)

    level: str = Field(description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    logger_name: str = Field(
        description="Application logger name for propagating loggers.",
    )
    diagnostic_format: str = Field(
        description="Log format for diagnostic records (< INFO). Includes filename:lineno.",
    )
    operational_format: str = Field(
        description="Log format for operational records (>= INFO). No filename:lineno.",
    )
    file: str | None = Field(description="Log file path (stderr if None)")
    enabled: bool = Field(
        description="Enable non-blocking logging via queue.",
    )
    log_dir: str | None = Field(
        description="Directory for rotating log files. None disables file logging.",
    )
    max_bytes: int = Field(
        description="Max log file size before rotation (bytes).",
    )
    backup_count: int = Field(
        description="Number of rotated log files to keep.",
    )


class ToolConfig(BaseModel):
    """Configuration for an external tool (ruff, pylint, pyright).

    Required. Configure via [tool.selma.tools.*] in pyproject.toml.
    """

    model_config = ConfigDict(frozen=True)

    enabled: bool = Field(description="Whether this tool is enabled")
    binary: str = Field(description="Path or name of the tool binary")
    args: tuple[str, ...] = Field(description="Extra CLI arguments")
    rcfile: str | None = Field(description="Config file path for the tool")
    fail_under: int = Field(description="Minimum score threshold")


class RulesFilterConfig(BaseModel):
    """Top-level rule filtering by code.

    All rules are active unless explicitly disabled.
    Configure via [tool.selma.rules] in pyproject.toml
    or SELMA_RULES_* env vars.
    """

    model_config = ConfigDict(frozen=True)

    disabled: tuple[str, ...] = Field(description="Rule codes to disable")
    codes: tuple[str, ...] = Field(
        description="Only run these rule codes (empty = all)"
    )
    exclude_codes: tuple[str, ...] = Field(description="Exclude these rule codes")


class ToolsConfig(BaseModel):
    """External tools configuration.

    Required. Configure via [tool.selma.tools] in pyproject.toml.
    """

    model_config = ConfigDict(frozen=True)

    ruff: ToolConfig = Field(description="Ruff linter configuration")
    pylint: ToolConfig = Field(description="Pylint configuration")
    pyright: ToolConfig = Field(description="Pyright type checker configuration")


class SelmaConfig(BaseModel):
    """Top-level immutable configuration.

    ALL values MUST be configured externally. No hardcoded paths,
    no hardcoded patterns, no hardcoded rule exclusions in source.

    Configuration sources (priority: CLI > env > pyproject.toml):
    - pyproject.toml [tool.selma] sections
    - Environment variables: SELMA_*
    - CLI arguments
    """

    model_config = ConfigDict(frozen=True)

    version: str = Field(description="Configuration version")
    name: str = Field(description="Project name")

    paths: PathsConfig = Field(description="Lint target paths")
    output: OutputConfig = Field(description="Output formatting config")
    execution: ExecutionConfig = Field(description="Execution behavior config")
    rules_filter: RulesFilterConfig = Field(description="Rule filtering config")
    tools: ToolsConfig = Field(description="External tools config")
    logging: LoggingConfig = Field(description="Logging config")
    directive: DirectivePathsConfig = Field(description="Directive paths config")
    schema_paths: SchemaPathsConfig = Field(description="Schema paths config")
