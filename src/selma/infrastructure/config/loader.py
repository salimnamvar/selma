"""Configuration loader — loads from pyproject.toml, env vars, CLI args.

Priority: CLI Arguments > Environment Variables > pyproject.toml

ALL configuration values MUST be provided from one of these sources.
No hardcoded defaults in the loader either.
"""

from __future__ import annotations

import os
from pathlib import Path
import tomllib
from typing import Any

from selma.domain.value_objects.result import Result
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

        Priority: CLI > env > toml.

        Preconditions:
            - a_config_path points to a valid pyproject.toml if provided.
            - a_cli_args is a dict of CLI arguments if provided.

        Postconditions:
            Returns Result.success with validated SelmaConfig, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on invalid config, missing required values,
                 or I/O error.
        """
        result: Result[SelmaConfig] = Result.failure("unreachable")
        b_continue = True

        toml_data: dict[str, Any] = {}
        if b_continue and a_config_path is not None:
            toml_result = self._load_toml(a_config_path)
            if b_continue and toml_result.is_failure():
                b_continue = False
                result = Result.failure(f"TOML error: {toml_result.message}")
            if b_continue and toml_result.is_success():
                toml_data = toml_result.unwrap()

        if b_continue:
            config_result = self._build_config(toml_data, a_cli_args)
            if config_result.is_failure():
                b_continue = False
                result = Result.failure(config_result.message)
            if b_continue:
                config = config_result.unwrap()
                self._cached_config = config
                validation = self._validator.validate(config)
                if validation.is_failure():
                    b_continue = False
                    result = Result.failure(f"Validation: {validation.message}")
                if b_continue:
                    result = Result.success(config)

        return result

    def get_cached(self) -> SelmaConfig | None:
        """Return the cached config, or None if not loaded."""
        return self._cached_config

    def _build_config(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[SelmaConfig]:
        """Build SelmaConfig from all sources.

        Every required field must be resolvable from toml, env, or cli.
        """
        b_continue = True
        result: Result[SelmaConfig] = Result.failure("unreachable")

        # Required sections
        directive_result = self._resolve_directive(a_toml, a_cli_args)
        if b_continue and directive_result.is_failure():
            b_continue = False
            result = Result.failure(directive_result.message)

        schema_result: Result[SchemaPathsConfig] = Result.failure("unreachable")
        if b_continue:
            schema_result = self._resolve_schema(a_toml, a_cli_args)
            if schema_result.is_failure():
                b_continue = False
                result = Result.failure(schema_result.message)

        paths_result: Result[PathsConfig] = Result.failure("unreachable")
        if b_continue:
            paths_result = self._build_paths(a_toml)
            if paths_result.is_failure():
                b_continue = False
                result = Result.failure(paths_result.message)

        output_result: Result[OutputConfig] = Result.failure("unreachable")
        if b_continue:
            output_result = self._build_output(a_toml, a_cli_args)
            if output_result.is_failure():
                b_continue = False
                result = Result.failure(output_result.message)

        execution_result: Result[ExecutionConfig] = Result.failure("unreachable")
        if b_continue:
            execution_result = self._build_execution(a_toml, a_cli_args)
            if execution_result.is_failure():
                b_continue = False
                result = Result.failure(execution_result.message)

        rules_result: Result[RulesFilterConfig] = Result.failure("unreachable")
        if b_continue:
            rules_result = self._build_rules_filter(a_toml, a_cli_args)
            if rules_result.is_failure():
                b_continue = False
                result = Result.failure(rules_result.message)

        tools_result: Result[ToolsConfig] = Result.failure("unreachable")
        if b_continue:
            tools_result = self._build_tools(a_toml)
            if tools_result.is_failure():
                b_continue = False
                result = Result.failure(tools_result.message)

        logging_result: Result[LoggingConfig] = Result.failure("unreachable")
        if b_continue:
            logging_result = self._build_logging(a_toml)
            if logging_result.is_failure():
                b_continue = False
                result = Result.failure(logging_result.message)

        if b_continue:
            config = SelmaConfig(
                version=a_toml.get("version", "0.1.0"),
                name=a_toml.get("name", "selma"),
                paths=paths_result.unwrap(),
                output=output_result.unwrap(),
                execution=execution_result.unwrap(),
                rules_filter=rules_result.unwrap(),
                tools=tools_result.unwrap(),
                logging=logging_result.unwrap(),
                directive=directive_result.unwrap(),
                schema_paths=schema_result.unwrap(),
            )

            # CLI positional paths override
            cli_paths = a_cli_args.get("paths") if a_cli_args else None
            if cli_paths:
                config = SelmaConfig(
                    version=config.version,
                    name=config.name,
                    paths=PathsConfig(
                        include=tuple(cli_paths),
                        exclude=config.paths.exclude,
                        extensions=config.paths.extensions,
                    ),
                    output=config.output,
                    execution=config.execution,
                    rules_filter=config.rules_filter,
                    tools=config.tools,
                    logging=config.logging,
                    directive=config.directive,
                    schema_paths=config.schema_paths,
                )

            result = Result.success(config)

        return result

    # ── Directive path resolution (required) ──────────────────────────────

    def _resolve_directive(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[DirectivePathsConfig]:
        """Resolve directive paths from CLI > env > toml."""
        toml_data = a_toml.get("directive", {})

        cli_root = (a_cli_args or {}).get("directive_root")
        cli_policy = (a_cli_args or {}).get("directive_policy_dir")
        cli_rule = (a_cli_args or {}).get("directive_rule_dir")

        env_root = os.environ.get(f"{_ENV_PREFIX}DIRECTIVE_ROOT")
        env_policy = os.environ.get(f"{_ENV_PREFIX}DIRECTIVE_POLICY_DIR")
        env_rule = os.environ.get(f"{_ENV_PREFIX}DIRECTIVE_RULE_DIR")

        root_str = cli_root or env_root or toml_data.get("root")
        policy_str = cli_policy or env_policy or toml_data.get("policy_dir")
        rule_str = cli_rule or env_rule or toml_data.get("rule_dir")

        if not root_str:
            return Result.failure(
                "Directive root path required. Set [tool.selma.directive.root], "
                + "SELMA_DIRECTIVE_ROOT, or --directive-root.",
            )
        if not policy_str:
            return Result.failure(
                "Directive policy_dir required. Set [tool.selma.directive.policy_dir], "
                + "SELMA_DIRECTIVE_POLICY_DIR, or --directive-policy-dir.",
            )
        if not rule_str:
            return Result.failure(
                "Directive rule_dir required. Set [tool.selma.directive.rule_dir], "
                + "SELMA_DIRECTIVE_RULE_DIR, or --directive-rule-dir.",
            )

        return Result.success(
            DirectivePathsConfig(
                root=Path(root_str),
                policy_dir=Path(policy_str),
                rule_dir=Path(rule_str),
            ),
        )

    # ── Schema path resolution (required) ─────────────────────────────────

    def _resolve_schema(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[SchemaPathsConfig]:
        """Resolve schema paths from CLI > env > toml."""
        toml_data = a_toml.get("schema", {})

        cli_root = (a_cli_args or {}).get("schema_root")
        cli_rule = (a_cli_args or {}).get("schema_rule_schema")
        cli_policy = (a_cli_args or {}).get("schema_policy_doctrine")

        env_root = os.environ.get(f"{_ENV_PREFIX}SCHEMA_ROOT")
        env_rule = os.environ.get(f"{_ENV_PREFIX}SCHEMA_RULE_SCHEMA")
        env_policy = os.environ.get(f"{_ENV_PREFIX}SCHEMA_POLICY_DOCTRINE")

        root_str = cli_root or env_root or toml_data.get("root")
        rule_str = cli_rule or env_rule or toml_data.get("rule_schema")
        policy_str = cli_policy or env_policy or toml_data.get("policy_doctrine")

        if not root_str:
            return Result.failure(
                "Schema root path required. Set [tool.selma.schema.root], "
                + "SELMA_SCHEMA_ROOT, or --schema-root.",
            )
        if not rule_str:
            return Result.failure(
                "Schema rule_schema path required. Set [tool.selma.schema.rule_schema], "
                + "SELMA_SCHEMA_RULE_SCHEMA, or --schema-rule-schema.",
            )
        if not policy_str:
            return Result.failure(
                "Schema policy_doctrine path required. Set "
                + "[tool.selma.schema.policy_doctrine], SELMA_SCHEMA_POLICY_DOCTRINE, "
                + "or --schema-policy-doctrine.",
            )

        return Result.success(
            SchemaPathsConfig(
                root=Path(root_str),
                rule_schema=Path(rule_str),
                policy_doctrine=Path(policy_str),
            ),
        )

    # ── TOML loading ──────────────────────────────────────────────────────

    def _load_toml(self, a_path: Path) -> Result[dict[str, Any]]:
        """Load from pyproject.toml [tool.selma] section."""
        result: Result[dict[str, Any]] = Result.failure("unreachable")
        try:
            with a_path.open("rb") as f:
                data: dict[str, Any] = tomllib.load(f)
            selma = data.get("tool", {}).get("selma", {})
            result = Result.success(selma)
        except (OSError, tomllib.TOMLDecodeError) as e:
            result = Result.failure(str(e))
        return result

    # ── Paths (lint targets, required) ────────────────────────────────────

    def _build_paths(self, a_toml: dict[str, Any]) -> Result[PathsConfig]:
        """Build paths config from toml > env."""
        data = a_toml.get("paths", {})

        include_str = os.environ.get(f"{_ENV_PREFIX}PATHS_INCLUDE")
        exclude_str = os.environ.get(f"{_ENV_PREFIX}PATHS_EXCLUDE")
        extensions_str = os.environ.get(f"{_ENV_PREFIX}PATHS_EXTENSIONS")

        include_raw = include_str.split(",") if include_str else data.get("include")
        exclude_raw = exclude_str.split(",") if exclude_str else data.get("exclude")
        extensions_raw = (
            extensions_str.split(",") if extensions_str else data.get("extensions")
        )

        if not include_raw:
            return Result.failure(
                "paths.include required. Set [tool.selma.paths.include] or "
                + "SELMA_PATHS_INCLUDE.",
            )
        if not exclude_raw:
            return Result.failure(
                "paths.exclude required. Set [tool.selma.paths.exclude] or "
                + "SELMA_PATHS_EXCLUDE.",
            )
        if not extensions_raw:
            return Result.failure(
                "paths.extensions required. Set [tool.selma.paths.extensions] or "
                + "SELMA_PATHS_EXTENSIONS.",
            )

        return Result.success(
            PathsConfig(
                include=tuple(include_raw),
                exclude=tuple(exclude_raw),
                extensions=tuple(extensions_raw),
            ),
        )

    # ── Output (required) ─────────────────────────────────────────────────

    def _build_output(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[OutputConfig]:
        """Build output config from toml > env > cli."""
        toml_data = a_toml.get("output", {})

        env_fmt = os.environ.get(f"{_ENV_PREFIX}OUTPUT_FORMAT")
        env_guide = os.environ.get(f"{_ENV_PREFIX}OUTPUT_GUIDE")
        env_file = os.environ.get(f"{_ENV_PREFIX}OUTPUT_FILE")
        env_color = os.environ.get(f"{_ENV_PREFIX}OUTPUT_COLOR")

        fmt = env_fmt or toml_data.get("format")
        if not fmt:
            return Result.failure(
                "output.format required. Set [tool.selma.output.format] or "
                + "SELMA_OUTPUT_FORMAT.",
            )

        guide_str = env_guide or toml_data.get("guide")
        if guide_str is None:
            return Result.failure(
                "output.guide required. Set [tool.selma.output.guide] or "
                + "SELMA_OUTPUT_GUIDE.",
            )
        guide = str(guide_str).lower() in ("true", "1", "yes")

        file = env_file or toml_data.get("file")

        color_str = env_color or toml_data.get("color")
        if color_str is None:
            return Result.failure(
                "output.color required. Set [tool.selma.output.color] or "
                + "SELMA_OUTPUT_COLOR.",
            )
        color = str(color_str).lower() in ("true", "1", "yes")

        if a_cli_args:
            cli_fmt = a_cli_args.get("format")
            if cli_fmt:
                fmt = cli_fmt
            if a_cli_args.get("guide"):
                guide = True
            cli_file = a_cli_args.get("output")
            if cli_file:
                file = cli_file
            if a_cli_args.get("no_color"):
                color = False

        return Result.success(
            OutputConfig(format=fmt, guide=guide, file=file, color=color)
        )

    # ── Execution (required) ──────────────────────────────────────────────

    def _build_execution(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[ExecutionConfig]:
        """Build execution config from toml > env > cli."""
        toml_data = a_toml.get("execution", {})

        env_skip_tools = os.environ.get(f"{_ENV_PREFIX}EXECUTION_SKIP_TOOLS")
        env_skip_ast = os.environ.get(f"{_ENV_PREFIX}EXECUTION_SKIP_AST")
        env_only = os.environ.get(f"{_ENV_PREFIX}EXECUTION_ONLY")
        env_workers = os.environ.get(f"{_ENV_PREFIX}EXECUTION_MAX_WORKERS")
        env_timeout = os.environ.get(f"{_ENV_PREFIX}EXECUTION_FILE_TIMEOUT")

        skip_tools_str = env_skip_tools or toml_data.get("skip_tools")
        if skip_tools_str is None:
            return Result.failure(
                "execution.skip_tools required. Set "
                + "[tool.selma.execution.skip_tools] or SELMA_EXECUTION_SKIP_TOOLS.",
            )
        skip_tools = str(skip_tools_str).lower() in ("true", "1", "yes")

        skip_ast_str = env_skip_ast or toml_data.get("skip_ast")
        if skip_ast_str is None:
            return Result.failure(
                "execution.skip_ast required. Set "
                + "[tool.selma.execution.skip_ast] or SELMA_EXECUTION_SKIP_AST.",
            )
        skip_ast = str(skip_ast_str).lower() in ("true", "1", "yes")

        only = env_only or toml_data.get("only")
        if only == "":
            only = None

        max_workers_str = env_workers or toml_data.get("max_workers")
        if max_workers_str is None:
            return Result.failure(
                "execution.max_workers required. Set "
                + "[tool.selma.execution.max_workers] or SELMA_EXECUTION_MAX_WORKERS.",
            )

        file_timeout_str = env_timeout or toml_data.get("file_timeout")
        if file_timeout_str is None:
            return Result.failure(
                "execution.file_timeout required. Set "
                + "[tool.selma.execution.file_timeout] or SELMA_EXECUTION_FILE_TIMEOUT.",
            )

        if a_cli_args:
            if a_cli_args.get("skip_tools"):
                skip_tools = True
            if a_cli_args.get("skip_ast"):
                skip_ast = True
            cli_only = a_cli_args.get("only")
            if cli_only:
                only = cli_only
            cli_workers = a_cli_args.get("max_workers")
            if cli_workers:
                max_workers_str = cli_workers
            cli_timeout = a_cli_args.get("file_timeout")
            if cli_timeout:
                file_timeout_str = cli_timeout

        return Result.success(
            ExecutionConfig(
                skip_tools=skip_tools,
                skip_ast=skip_ast,
                only=only,
                max_workers=int(max_workers_str),
                file_timeout=int(file_timeout_str),
            ),
        )

    # ── Rules filter (required) ───────────────────────────────────────────

    def _build_rules_filter(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[RulesFilterConfig]:
        """Build rules filter from toml > env > cli."""
        toml_data = a_toml.get("rules", {})

        env_disabled = os.environ.get(f"{_ENV_PREFIX}RULES_DISABLED")
        env_codes = os.environ.get(f"{_ENV_PREFIX}RULES_CODES")
        env_exclude = os.environ.get(f"{_ENV_PREFIX}RULES_EXCLUDE_CODES")

        disabled_raw = (
            env_disabled.split(",") if env_disabled else toml_data.get("disabled")
        )
        codes_raw = env_codes.split(",") if env_codes else toml_data.get("codes")
        exclude_raw = (
            env_exclude.split(",") if env_exclude else toml_data.get("exclude_codes")
        )

        if disabled_raw is None:
            return Result.failure(
                "rules.disabled required (use [] for none). Set "
                + "[tool.selma.rules.disabled] or SELMA_RULES_DISABLED.",
            )
        if codes_raw is None:
            return Result.failure(
                "rules.codes required (use [] for all). Set "
                + "[tool.selma.rules.codes] or SELMA_RULES_CODES.",
            )
        if exclude_raw is None:
            return Result.failure(
                "rules.exclude_codes required (use [] for none). Set "
                + "[tool.selma.rules.exclude_codes] or SELMA_RULES_EXCLUDE_CODES.",
            )

        disabled = tuple(c.strip() for c in disabled_raw if c.strip())
        codes = tuple(c.strip() for c in codes_raw if c.strip())
        exclude_codes = tuple(c.strip() for c in exclude_raw if c.strip())

        if a_cli_args:
            cli_codes = a_cli_args.get("codes")
            if cli_codes:
                codes = tuple(cli_codes)
            cli_exclude = a_cli_args.get("exclude_codes")
            if cli_exclude:
                exclude_codes = tuple(cli_exclude)
            cli_disable = a_cli_args.get("disable")
            if cli_disable:
                disabled = tuple(cli_disable)

        return Result.success(
            RulesFilterConfig(
                disabled=disabled,
                codes=codes,
                exclude_codes=exclude_codes,
            ),
        )

    # ── Tools (required) ──────────────────────────────────────────────────

    def _build_tools(self, a_toml: dict[str, Any]) -> Result[ToolsConfig]:
        """Build tools config from toml."""
        data = a_toml.get("tools", {})

        ruff_data = data.get("ruff")
        pylint_data = data.get("pylint")
        pyright_data = data.get("pyright")

        if not ruff_data:
            return Result.failure(
                "tools.ruff required. Set [tool.selma.tools.ruff] in pyproject.toml.",
            )
        if not pylint_data:
            return Result.failure(
                "tools.pylint required. Set [tool.selma.tools.pylint] in pyproject.toml.",
            )
        if not pyright_data:
            return Result.failure(
                "tools.pyright required. Set [tool.selma.tools.pyright] in pyproject.toml.",
            )

        ruff_result = self._build_tool_config("ruff", ruff_data)
        if ruff_result.is_failure():
            return Result.failure(ruff_result.message)
        pylint_result = self._build_tool_config("pylint", pylint_data)
        if pylint_result.is_failure():
            return Result.failure(pylint_result.message)
        pyright_result = self._build_tool_config("pyright", pyright_data)
        if pyright_result.is_failure():
            return Result.failure(pyright_result.message)

        return Result.success(
            ToolsConfig(
                ruff=ruff_result.unwrap(),
                pylint=pylint_result.unwrap(),
                pyright=pyright_result.unwrap(),
            ),
        )

    def _build_tool_config(
        self,
        a_name: str,
        a_data: dict[str, Any],
    ) -> Result[ToolConfig]:
        """Build a single tool config from toml data."""
        enabled = a_data.get("enabled")
        if enabled is None:
            return Result.failure(f"tools.{a_name}.enabled required.")
        binary = a_data.get("binary")
        if not binary:
            return Result.failure(f"tools.{a_name}.binary required.")
        args_raw = a_data.get("args")
        if args_raw is None:
            return Result.failure(f"tools.{a_name}.args required (use [] for none).")
        fail_under = a_data.get("fail_under")
        if fail_under is None:
            return Result.failure(f"tools.{a_name}.fail_under required.")

        return Result.success(
            ToolConfig(
                enabled=bool(enabled),
                binary=binary,
                args=tuple(args_raw),
                rcfile=a_data.get("rcfile"),
                fail_under=int(fail_under),
            ),
        )

    # ── Logging (required) ────────────────────────────────────────────────

    def _build_logging(self, a_toml: dict[str, Any]) -> Result[LoggingConfig]:
        """Build logging config from toml > env."""
        toml_data = a_toml.get("logging", {})

        env_level = os.environ.get(f"{_ENV_PREFIX}LOGGING_LEVEL")
        env_format = os.environ.get(f"{_ENV_PREFIX}LOGGING_FORMAT")
        env_file = os.environ.get(f"{_ENV_PREFIX}LOGGING_FILE")

        level = env_level or toml_data.get("level")
        if not level:
            return Result.failure(
                "logging.level required. Set [tool.selma.logging.level] or "
                + "SELMA_LOGGING_LEVEL.",
            )

        fmt = env_format or toml_data.get("format")
        if not fmt:
            return Result.failure(
                "logging.format required. Set [tool.selma.logging.format] or "
                + "SELMA_LOGGING_FORMAT.",
            )

        file = env_file or toml_data.get("file")

        return Result.success(LoggingConfig(level=level, format=fmt, file=file))
