"""Configuration system — loads from pyproject.toml, env vars, CLI.

Rule definitions live in directive/rule/*.json (schema-driven).
Policy definitions live in directive/policy/*.yaml.
Schema definitions live in schema/*.json and schema/*.yaml.
This module handles infrastructure config and path resolution.
"""

from selma.infrastructure.config.loader import ConfigLoader
from selma.infrastructure.config.models import DirectivePathsConfig
from selma.infrastructure.config.models import ExecutionConfig
from selma.infrastructure.config.models import LoggingConfig
from selma.infrastructure.config.models import OutputConfig
from selma.infrastructure.config.models import PathsConfig
from selma.infrastructure.config.models import RulesFilterConfig
from selma.infrastructure.config.models import SchemaPathsConfig
from selma.infrastructure.config.models import SelmaConfig
from selma.infrastructure.config.models import ToolConfig
from selma.infrastructure.config.models import ToolsConfig
from selma.infrastructure.config.validator import ConfigValidator

__all__: tuple[str, ...] = (
    "ConfigLoader",
    "ConfigValidator",
    "DirectivePathsConfig",
    "ExecutionConfig",
    "LoggingConfig",
    "OutputConfig",
    "PathsConfig",
    "RulesFilterConfig",
    "SchemaPathsConfig",
    "SelmaConfig",
    "ToolConfig",
    "ToolsConfig",
)
