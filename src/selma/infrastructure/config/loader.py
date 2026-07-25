"""Configuration loader — loads from pyproject.toml, env vars, CLI args.

Priority: CLI Arguments > Environment Variables > pyproject.toml > Defaults
"""

from __future__ import annotations

import os
from pathlib import Path
import tomllib
from typing import Any

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.models import ExecutionConfig
from selma.infrastructure.config.models import LoggingConfig
from selma.infrastructure.config.models import OutputConfig
from selma.infrastructure.config.models import PathsConfig
from selma.infrastructure.config.models import RulesConfig
from selma.infrastructure.config.models import RulesFilterConfig
from selma.infrastructure.config.models import SC010Config
from selma.infrastructure.config.models import SelmaConfig
from selma.infrastructure.config.models import ToolConfig
from selma.infrastructure.config.models import ToolsConfig
from selma.infrastructure.config.validator import ConfigValidator

_ENV_PREFIX = "SELMA_"


class ConfigLoader:
    """Load configuration from all sources with priority."""

    def __init__(self) -> None:
        self._validator = ConfigValidator()
        self._cached_config: SelmaConfig | None = None

    def load(
        self,
        a_config_path: Path | None = None,
        a_cli_args: dict[str, Any] | None = None,
    ) -> Result[SelmaConfig]:
        """Load configuration with priority.

        Priority: CLI > env > toml > defaults.

        Preconditions:
            - a_config_path points to a valid pyproject.toml if
              provided.
            - a_cli_args is a dict of CLI arguments if provided.

        Postconditions:
            - Returns Result.success with validated SelmaConfig,
              or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on invalid config or I/O error.
        """
        config = self._load_defaults()
        result: Result[SelmaConfig] = Result.failure("unreachable")
        b_continue = True

        if b_continue and a_config_path is not None:
            toml_result = self._load_toml(a_config_path)
            if b_continue and toml_result.is_failure():
                b_continue = False
                msg = f"TOML error: {toml_result.message}"
                result = Result.failure(msg)
            if b_continue and toml_result.is_success():
                config = self._merge_toml(config, toml_result.value)

        if b_continue:
            config = self._load_env(config)

        if b_continue and a_cli_args is not None:
            config = self._load_cli(config, a_cli_args)

        if b_continue:
            self._cached_config = config
            validation = self._validator.validate(config)
            if b_continue and validation.is_failure():
                b_continue = False
                msg = f"Validation: {validation.message}"
                result = Result.failure(msg)
            if b_continue:
                result = Result.success(config)

        return result

    def get_cached(self) -> SelmaConfig | None:
        """Return the cached config, or None if not loaded."""
        return self._cached_config

    def _load_defaults(self) -> SelmaConfig:
        """Create default configuration."""
        return SelmaConfig()

    def _load_toml(self, a_path: Path) -> Result[dict[str, Any]]:
        """Load from pyproject.toml [tool.selma] section.

        Preconditions:
            - a_path exists and is readable.

        Postconditions:
            - Returns Result.success with toml dict, or
              Result.failure.

        Side Effects: None.
        Resource: Reads file.
        Failure: Returns Failure on I/O or parse error.
        """
        b_continue = True
        result: Result[dict[str, Any]] = Result.failure("unreachable")
        try:
            data: dict[str, Any] = {}
            if b_continue:
                with a_path.open("rb") as f:
                    data = tomllib.load(f)
            if b_continue:
                selma = data.get("tool", {}).get("selma", {})
                result = Result.success(selma)
        except (OSError, tomllib.TOMLDecodeError) as e:
            result = Result.failure(str(e))
        return result

    def _merge_toml(
        self,
        a_base: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge TOML config into base config."""
        result = a_base
        result = self._merge_paths_toml(result, a_toml)
        result = self._merge_output_toml(result, a_toml)
        result = self._merge_execution_toml(result, a_toml)
        result = self._merge_rules_toml(result, a_toml)
        result = self._merge_tools_toml(result, a_toml)
        return self._merge_logging_toml(result, a_toml)

    def _merge_paths_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge paths from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("paths")
        if b_continue and data:
            paths = PathsConfig(
                include=tuple(
                    data.get("include", a_config.paths.include)
                ),
                exclude=tuple(
                    data.get("exclude", a_config.paths.exclude)
                ),
                extensions=tuple(
                    data.get(
                        "extensions", a_config.paths.extensions
                    )
                ),
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=paths,
                output=result.output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result

    def _merge_output_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge output from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("output")
        if b_continue and data:
            output = OutputConfig(
                format=data.get("format", result.output.format),
                guide=data.get("guide", result.output.guide),
                file=data.get("file", result.output.file),
                color=data.get("color", result.output.color),
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=result.paths,
                output=output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result

    def _merge_execution_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge execution from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("execution")
        if b_continue and data:
            ex = result.execution
            only_val = data.get("only", ex.only)
            if only_val == "":
                only_val = None
            execution = ExecutionConfig(
                skip_tools=data.get("skip_tools", ex.skip_tools),
                skip_ast=data.get("skip_ast", ex.skip_ast),
                only=only_val,
                max_workers=data.get(
                    "max_workers", ex.max_workers
                ),
                file_timeout=data.get(
                    "file_timeout", ex.file_timeout
                ),
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=result.paths,
                output=result.output,
                execution=execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result

    def _merge_rules_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge rules from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("rules")
        if b_continue and data:
            rf = result.rules_filter
            rules_filter = RulesFilterConfig(
                disabled=tuple(
                    data.get("disabled", rf.disabled)
                ),
                codes=tuple(
                    data.get("codes", rf.codes)
                ),
                exclude_codes=tuple(
                    data.get("exclude_codes", rf.exclude_codes)
                ),
            )
            rules = self._merge_rules_data(
                result.rules, data
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=result.paths,
                output=result.output,
                execution=result.execution,
                rules_filter=rules_filter,
                rules=rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result

    def _merge_rules_data(
        self,
        a_rules: RulesConfig,
        a_data: dict[str, Any],
    ) -> RulesConfig:
        """Merge rule-specific TOML data."""
        b_continue = True
        result = a_rules

        sc010_data = a_data.get("sc010")
        if b_continue and sc010_data:
            old = result.sc010
            result = RulesConfig(
                sc001=result.sc001,
                sc002=result.sc002,
                sc003=result.sc003,
                sc004=result.sc004,
                sc005=result.sc005,
                sc007=result.sc007,
                sc010=SC010Config(
                    enabled=sc010_data.get(
                        "enabled", old.enabled
                    ),
                    severity=sc010_data.get(
                        "severity", old.severity
                    ),
                    max_lines=sc010_data.get(
                        "max_lines", old.max_lines
                    ),
                    count_nested=sc010_data.get(
                        "count_nested", old.count_nested
                    ),
                    exclude_non_executable=sc010_data.get(
                        "exclude_non_executable",
                        old.exclude_non_executable,
                    ),
                ),
                sc011=result.sc011,
                sc013=result.sc013,
                sc022=result.sc022,
                sc024=result.sc024,
                sc025=result.sc025,
                sc031=result.sc031,
                sc033=result.sc033,
                sc041=result.sc041,
                sc042=result.sc042,
                sc052=result.sc052,
                sc060=result.sc060,
                sc061=result.sc061,
                sc062=result.sc062,
                sc065=result.sc065,
                sc070=result.sc070,
                sc071=result.sc071,
                sc080=result.sc080,
                sc090=result.sc090,
                sc092=result.sc092,
                sc100=result.sc100,
                sc101=result.sc101,
                sc104=result.sc104,
                sc114=result.sc114,
                sc115=result.sc115,
                no_print=result.no_print,
                todo_format=result.todo_format,
                a_prefix=result.a_prefix,
                mutable_default=result.mutable_default,
            )

        return result

    def _merge_tools_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge tools from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("tools")
        if b_continue and data:
            tools = self._merge_tools_data(
                result.tools, data
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=result.paths,
                output=result.output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=tools,
                logging=result.logging,
            )
        return result

    def _merge_tools_data(
        self,
        a_tools: ToolsConfig,
        a_data: dict[str, Any],
    ) -> ToolsConfig:
        """Merge tool-specific TOML data."""
        b_continue = True
        result = a_tools

        ruff_data = a_data.get("ruff")
        if b_continue and ruff_data:
            old = result.ruff
            result = ToolsConfig(
                ruff=ToolConfig(
                    enabled=ruff_data.get(
                        "enabled", old.enabled
                    ),
                    binary=ruff_data.get(
                        "binary", old.binary
                    ),
                    args=tuple(
                        ruff_data.get("args", old.args)
                    ),
                    rcfile=ruff_data.get(
                        "rcfile", old.rcfile
                    ),
                    fail_under=ruff_data.get(
                        "fail_under", old.fail_under
                    ),
                ),
                pylint=result.pylint,
                pyright=result.pyright,
            )

        pylint_data = a_data.get("pylint")
        if b_continue and pylint_data:
            old = result.pylint
            result = ToolsConfig(
                ruff=result.ruff,
                pylint=ToolConfig(
                    enabled=pylint_data.get(
                        "enabled", old.enabled
                    ),
                    binary=pylint_data.get(
                        "binary", old.binary
                    ),
                    args=tuple(
                        pylint_data.get("args", old.args)
                    ),
                    rcfile=pylint_data.get(
                        "rcfile", old.rcfile
                    ),
                    fail_under=pylint_data.get(
                        "fail_under", old.fail_under
                    ),
                ),
                pyright=result.pyright,
            )

        pyright_data = a_data.get("pyright")
        if b_continue and pyright_data:
            old = result.pyright
            result = ToolsConfig(
                ruff=result.ruff,
                pylint=result.pylint,
                pyright=ToolConfig(
                    enabled=pyright_data.get(
                        "enabled", old.enabled
                    ),
                    binary=pyright_data.get(
                        "binary", old.binary
                    ),
                    args=tuple(
                        pyright_data.get("args", old.args)
                    ),
                    rcfile=pyright_data.get(
                        "rcfile", old.rcfile
                    ),
                    fail_under=pyright_data.get(
                        "fail_under", old.fail_under
                    ),
                ),
            )

        return result

    def _merge_logging_toml(
        self,
        a_config: SelmaConfig,
        a_toml: dict[str, Any],
    ) -> SelmaConfig:
        """Merge logging from TOML."""
        b_continue = True
        result = a_config
        data = a_toml.get("logging")
        if b_continue and data:
            log_config = LoggingConfig(
                level=data.get("level", result.logging.level),
                format=data.get(
                    "format", result.logging.format
                ),
                file=data.get("file", result.logging.file),
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=result.paths,
                output=result.output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=log_config,
            )
        return result

    def _load_env(
        self,
        a_config: SelmaConfig,
    ) -> SelmaConfig:
        """Load from environment variables."""
        result = a_config
        result = self._env_paths(result)
        result = self._env_output(result)
        result = self._env_execution(result)
        result = self._env_rules(result)
        return self._env_logging(result)

    def _env_paths(self, a_config: SelmaConfig) -> SelmaConfig:
        """Load paths from env."""
        b_continue = True
        result = a_config
        val = os.environ.get(f"{_ENV_PREFIX}PATHS")
        if b_continue and val:
            paths = PathsConfig(
                include=tuple(
                    p.strip() for p in val.split(",")
                ),
                exclude=result.paths.exclude,
                extensions=result.paths.extensions,
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=paths,
                output=result.output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result

    def _env_output(
        self,
        a_config: SelmaConfig,
    ) -> SelmaConfig:
        """Load output from env."""
        result = a_config
        format_val = os.environ.get(
            f"{_ENV_PREFIX}OUTPUT_FORMAT"
        )
        if format_val:
            result = self._set_output(
                result,
                a_format=format_val,
            )
        guide_val = os.environ.get(
            f"{_ENV_PREFIX}OUTPUT_GUIDE"
        )
        if guide_val:
            result = self._set_output(
                result,
                guide=guide_val.lower() in ("true", "1", "yes"),
            )
        file_val = os.environ.get(
            f"{_ENV_PREFIX}OUTPUT_FILE"
        )
        if file_val:
            result = self._set_output(
                result,
                file=file_val,
            )
        color_val = os.environ.get(
            f"{_ENV_PREFIX}OUTPUT_COLOR"
        )
        if color_val:
            result = self._set_output(
                result,
                color=color_val.lower() in ("true", "1", "yes"),
            )
        return result

    def _set_output(
        self,
        a_config: SelmaConfig,
        *,
        a_format: str | None = None,
        guide: bool | None = None,
        file: str | None = None,
        color: bool | None = None,
    ) -> SelmaConfig:
        """Set output config values."""
        o = a_config.output
        output = OutputConfig(
            format=a_format if a_format is not None else o.format,
            guide=guide if guide is not None else o.guide,
            file=file if file is not None else o.file,
            color=color if color is not None else o.color,
        )
        return SelmaConfig(
            version=a_config.version,
            name=a_config.name,
            paths=a_config.paths,
            output=output,
            execution=a_config.execution,
            rules_filter=a_config.rules_filter,
            rules=a_config.rules,
            tools=a_config.tools,
            logging=a_config.logging,
        )

    def _env_execution(
        self,
        a_config: SelmaConfig,
    ) -> SelmaConfig:
        """Load execution from env."""
        result = a_config
        skip_tools = os.environ.get(
            f"{_ENV_PREFIX}EXECUTION_SKIP_TOOLS"
        )
        if skip_tools:
            result = self._set_execution(
                result,
                skip_tools=skip_tools.lower()
                in ("true", "1", "yes"),
            )
        skip_ast = os.environ.get(
            f"{_ENV_PREFIX}EXECUTION_SKIP_AST"
        )
        if skip_ast:
            result = self._set_execution(
                result,
                skip_ast=skip_ast.lower()
                in ("true", "1", "yes"),
            )
        only = os.environ.get(
            f"{_ENV_PREFIX}EXECUTION_ONLY"
        )
        if only:
            result = self._set_execution(
                result, only=only
            )
        max_workers = os.environ.get(
            f"{_ENV_PREFIX}EXECUTION_MAX_WORKERS"
        )
        if max_workers:
            result = self._set_execution(
                result, max_workers=int(max_workers)
            )
        return result

    def _set_execution(
        self,
        a_config: SelmaConfig,
        *,
        skip_tools: bool | None = None,
        skip_ast: bool | None = None,
        only: str | None = None,
        max_workers: int | None = None,
        file_timeout: int | None = None,
    ) -> SelmaConfig:
        """Set execution config values."""
        e = a_config.execution
        execution = ExecutionConfig(
            skip_tools=(
                skip_tools
                if skip_tools is not None
                else e.skip_tools
            ),
            skip_ast=(
                skip_ast
                if skip_ast is not None
                else e.skip_ast
            ),
            only=only if only is not None else e.only,
            max_workers=(
                max_workers
                if max_workers is not None
                else e.max_workers
            ),
            file_timeout=(
                file_timeout
                if file_timeout is not None
                else e.file_timeout
            ),
        )
        return SelmaConfig(
            version=a_config.version,
            name=a_config.name,
            paths=a_config.paths,
            output=a_config.output,
            execution=execution,
            rules_filter=a_config.rules_filter,
            rules=a_config.rules,
            tools=a_config.tools,
            logging=a_config.logging,
        )

    def _env_rules(
        self,
        a_config: SelmaConfig,
    ) -> SelmaConfig:
        """Load rules from env."""
        result = a_config
        disabled = os.environ.get(
            f"{_ENV_PREFIX}RULES_DISABLED"
        )
        if disabled:
            result = self._set_rules_filter(
                result,
                disabled=tuple(
                    c.strip() for c in disabled.split(",")
                ),
            )
        codes = os.environ.get(
            f"{_ENV_PREFIX}RULES_CODES"
        )
        if codes:
            result = self._set_rules_filter(
                result,
                codes=tuple(
                    c.strip() for c in codes.split(",")
                ),
            )
        exclude = os.environ.get(
            f"{_ENV_PREFIX}RULES_EXCLUDE_CODES"
        )
        if exclude:
            result = self._set_rules_filter(
                result,
                exclude_codes=tuple(
                    c.strip() for c in exclude.split(",")
                ),
            )
        sc010_max = os.environ.get(
            f"{_ENV_PREFIX}RULES_SC010_MAX_LINES"
        )
        if sc010_max:
            result = self._set_sc010_max(
                result, int(sc010_max)
            )
        return result

    def _set_rules_filter(
        self,
        a_config: SelmaConfig,
        *,
        disabled: tuple[str, ...] | None = None,
        codes: tuple[str, ...] | None = None,
        exclude_codes: tuple[str, ...] | None = None,
    ) -> SelmaConfig:
        """Set rules filter config values."""
        rf = a_config.rules_filter
        rules_filter = RulesFilterConfig(
            disabled=(
                disabled
                if disabled is not None
                else rf.disabled
            ),
            codes=(
                codes if codes is not None else rf.codes
            ),
            exclude_codes=(
                exclude_codes
                if exclude_codes is not None
                else rf.exclude_codes
            ),
        )
        return SelmaConfig(
            version=a_config.version,
            name=a_config.name,
            paths=a_config.paths,
            output=a_config.output,
            execution=a_config.execution,
            rules_filter=rules_filter,
            rules=a_config.rules,
            tools=a_config.tools,
            logging=a_config.logging,
        )

    def _set_sc010_max(
        self,
        a_config: SelmaConfig,
        a_max_lines: int,
    ) -> SelmaConfig:
        """Set SC010 max_lines."""
        old = a_config.rules.sc010
        rules = RulesConfig(
            sc001=a_config.rules.sc001,
            sc002=a_config.rules.sc002,
            sc003=a_config.rules.sc003,
            sc004=a_config.rules.sc004,
            sc005=a_config.rules.sc005,
            sc007=a_config.rules.sc007,
            sc010=SC010Config(
                enabled=old.enabled,
                severity=old.severity,
                max_lines=a_max_lines,
                count_nested=old.count_nested,
                exclude_non_executable=(
                    old.exclude_non_executable
                ),
            ),
            sc011=a_config.rules.sc011,
            sc013=a_config.rules.sc013,
            sc022=a_config.rules.sc022,
            sc024=a_config.rules.sc024,
            sc025=a_config.rules.sc025,
            sc031=a_config.rules.sc031,
            sc033=a_config.rules.sc033,
            sc041=a_config.rules.sc041,
            sc042=a_config.rules.sc042,
            sc052=a_config.rules.sc052,
            sc060=a_config.rules.sc060,
            sc061=a_config.rules.sc061,
            sc062=a_config.rules.sc062,
            sc065=a_config.rules.sc065,
            sc070=a_config.rules.sc070,
            sc071=a_config.rules.sc071,
            sc080=a_config.rules.sc080,
            sc090=a_config.rules.sc090,
            sc092=a_config.rules.sc092,
            sc100=a_config.rules.sc100,
            sc101=a_config.rules.sc101,
            sc104=a_config.rules.sc104,
            sc114=a_config.rules.sc114,
            sc115=a_config.rules.sc115,
            no_print=a_config.rules.no_print,
            todo_format=a_config.rules.todo_format,
            a_prefix=a_config.rules.a_prefix,
            mutable_default=a_config.rules.mutable_default,
        )
        return SelmaConfig(
            version=a_config.version,
            name=a_config.name,
            paths=a_config.paths,
            output=a_config.output,
            execution=a_config.execution,
            rules_filter=a_config.rules_filter,
            rules=rules,
            tools=a_config.tools,
            logging=a_config.logging,
        )

    def _env_logging(
        self,
        a_config: SelmaConfig,
    ) -> SelmaConfig:
        """Load logging from env."""
        result = a_config
        level = os.environ.get(
            f"{_ENV_PREFIX}LOGGING_LEVEL"
        )
        if level:
            result = self._set_logging(
                result, level=level
            )
        log_file = os.environ.get(
            f"{_ENV_PREFIX}LOGGING_FILE"
        )
        if log_file:
            result = self._set_logging(
                result, file=log_file
            )
        return result

    def _set_logging(
        self,
        a_config: SelmaConfig,
        *,
        level: str | None = None,
        file: str | None = None,
    ) -> SelmaConfig:
        """Set logging config values."""
        log_cfg = a_config.logging
        log_config = LoggingConfig(
            level=level if level is not None else log_cfg.level,
            format=log_cfg.format,
            file=file if file is not None else log_cfg.file,
        )
        return SelmaConfig(
            version=a_config.version,
            name=a_config.name,
            paths=a_config.paths,
            output=a_config.output,
            execution=a_config.execution,
            rules_filter=a_config.rules_filter,
            rules=a_config.rules,
            tools=a_config.tools,
            logging=log_config,
        )

    def _load_cli(
        self,
        a_config: SelmaConfig,
        a_args: dict[str, Any],
    ) -> SelmaConfig:
        """Load from CLI arguments."""
        result = a_config
        format_val = a_args.get("format")
        if format_val:
            result = self._set_output(
                result, a_format=format_val
            )
        if a_args.get("guide"):
            result = self._set_output(result, guide=True)
        output_file = a_args.get("output")
        if output_file:
            result = self._set_output(
                result, file=output_file
            )
        if a_args.get("no_color"):
            result = self._set_output(result, color=False)
        if a_args.get("skip_tools"):
            result = self._set_execution(
                result, skip_tools=True
            )
        if a_args.get("skip_ast"):
            result = self._set_execution(
                result, skip_ast=True
            )
        only_val = a_args.get("only")
        if only_val:
            result = self._set_execution(
                result, only=only_val
            )
        codes_val = a_args.get("codes")
        if codes_val:
            result = self._set_rules_filter(
                result, codes=tuple(codes_val)
            )
        exclude_val = a_args.get("exclude_codes")
        if exclude_val:
            result = self._set_rules_filter(
                result,
                exclude_codes=tuple(exclude_val),
            )
        disable_val = a_args.get("disable")
        if disable_val:
            result = self._set_rules_filter(
                result,
                disabled=tuple(disable_val),
            )
        max_workers = a_args.get("max_workers")
        if max_workers:
            result = self._set_execution(
                result, max_workers=int(max_workers)
            )
        file_timeout = a_args.get("file_timeout")
        if file_timeout:
            result = self._set_execution(
                result, file_timeout=int(file_timeout)
            )
        paths_val = a_args.get("paths")
        if paths_val:
            paths = PathsConfig(
                include=tuple(paths_val),
                exclude=result.paths.exclude,
                extensions=result.paths.extensions,
            )
            result = SelmaConfig(
                version=result.version,
                name=result.name,
                paths=paths,
                output=result.output,
                execution=result.execution,
                rules_filter=result.rules_filter,
                rules=result.rules,
                tools=result.tools,
                logging=result.logging,
            )
        return result
