"""Configuration loader — loads from pyproject.toml, env vars, CLI args.

Priority: CLI Arguments > Environment Variables > pyproject.toml

ALL configuration values MUST be provided from one of these sources.
No hardcoded defaults in the loader either.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import tomllib
from typing import Any
from typing import cast

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

logger = logging.getLogger(__name__)

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
                msg = f"TOML error: {toml_result.message}"
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue and toml_result.is_success():
                toml_data = toml_result.unwrap()

        if b_continue:
            config_result = self._build_config(toml_data, a_cli_args)
            if config_result.is_failure():
                b_continue = False
                msg = config_result.message
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue:
                config = config_result.unwrap()
                self._cached_config = config
                validation = self._validator.validate(config)
                if validation.is_failure():
                    b_continue = False
                    msg = f"Validation: {validation.message}"
                    logger.warning(msg)
                    result = Result.failure(msg)
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
            msg = directive_result.message
            logger.warning(msg)
            result = Result.failure(msg)

        schema_result: Result[SchemaPathsConfig] = Result.failure("unreachable")
        if b_continue:
            schema_result = self._resolve_schema(a_toml, a_cli_args)
            if schema_result.is_failure():
                b_continue = False
                msg = schema_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        paths_result: Result[PathsConfig] = Result.failure("unreachable")
        if b_continue:
            paths_result = self._build_paths(a_toml)
            if paths_result.is_failure():
                b_continue = False
                msg = paths_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        output_result: Result[OutputConfig] = Result.failure("unreachable")
        if b_continue:
            output_result = self._build_output(a_toml, a_cli_args)
            if output_result.is_failure():
                b_continue = False
                msg = output_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        execution_result: Result[ExecutionConfig] = Result.failure("unreachable")
        if b_continue:
            execution_result = self._build_execution(a_toml, a_cli_args)
            if execution_result.is_failure():
                b_continue = False
                msg = execution_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        rules_result: Result[RulesFilterConfig] = Result.failure("unreachable")
        if b_continue:
            rules_result = self._build_rules_filter(a_toml, a_cli_args)
            if rules_result.is_failure():
                b_continue = False
                msg = rules_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        tools_result: Result[ToolsConfig] = Result.failure("unreachable")
        if b_continue:
            tools_result = self._build_tools(a_toml)
            if tools_result.is_failure():
                b_continue = False
                msg = tools_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        logging_result: Result[LoggingConfig] = Result.failure("unreachable")
        if b_continue:
            logging_result = self._build_logging(a_toml)
            if logging_result.is_failure():
                b_continue = False
                msg = logging_result.message
                logger.warning(msg)
                result = Result.failure(msg)

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
        b_continue = True
        result: Result[DirectivePathsConfig] = Result.failure("unreachable")
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

        if b_continue and not root_str:
            b_continue = False
            msg = (
                "Directive root path required. Set [tool.selma.directive.root], "
                + "SELMA_DIRECTIVE_ROOT, or --directive-root."
            )
            logger.warning(msg)
            msg = (
                "Directive root path required. Set [tool.selma.directive.root], "
                + "SELMA_DIRECTIVE_ROOT, or --directive-root."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not policy_str:
            b_continue = False
            msg = (
                "Directive policy_dir required. Set [tool.selma.directive.policy_dir], "
                + "SELMA_DIRECTIVE_POLICY_DIR, or --directive-policy-dir."
            )
            logger.warning(msg)
            msg = (
                "Directive policy_dir required. Set [tool.selma.directive.policy_dir], "
                + "SELMA_DIRECTIVE_POLICY_DIR, or --directive-policy-dir."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not rule_str:
            b_continue = False
            msg = (
                "Directive rule_dir required. Set [tool.selma.directive.rule_dir], "
                + "SELMA_DIRECTIVE_RULE_DIR, or --directive-rule-dir."
            )
            logger.warning(msg)
            msg = (
                "Directive rule_dir required. Set [tool.selma.directive.rule_dir], "
                + "SELMA_DIRECTIVE_RULE_DIR, or --directive-rule-dir."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = Result.success(
                DirectivePathsConfig(
                    root=Path(root_str),
                    policy_dir=Path(policy_str),
                    rule_dir=Path(rule_str),
                ),
            )
        return result

    # ── Schema path resolution (required) ─────────────────────────────────

    def _resolve_schema(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[SchemaPathsConfig]:
        """Resolve schema paths from CLI > env > toml."""
        b_continue = True
        result: Result[SchemaPathsConfig] = Result.failure("unreachable")
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

        if b_continue and not root_str:
            b_continue = False
            msg = (
                "Schema root path required. Set [tool.selma.schema.root], "
                + "SELMA_SCHEMA_ROOT, or --schema-root."
            )
            logger.warning(msg)
            msg = (
                "Schema root path required. Set [tool.selma.schema.root], "
                + "SELMA_SCHEMA_ROOT, or --schema-root."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not rule_str:
            b_continue = False
            msg = (
                "Schema rule_schema path required. Set [tool.selma.schema.rule_schema], "
                + "SELMA_SCHEMA_RULE_SCHEMA, or --schema-rule-schema."
            )
            logger.warning(msg)
            msg = (
                "Schema rule_schema path required. Set [tool.selma.schema.rule_schema], "
                + "SELMA_SCHEMA_RULE_SCHEMA, or --schema-rule-schema."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not policy_str:
            b_continue = False
            msg = (
                "Schema policy_doctrine path required. Set "
                + "[tool.selma.schema.policy_doctrine], SELMA_SCHEMA_POLICY_DOCTRINE, "
                + "or --schema-policy-doctrine."
            )
            logger.warning(msg)
            msg = (
                "Schema policy_doctrine path required. Set "
                + "[tool.selma.schema.policy_doctrine], SELMA_SCHEMA_POLICY_DOCTRINE, "
                + "or --schema-policy-doctrine."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = Result.success(
                SchemaPathsConfig(
                    root=Path(root_str),
                    rule_schema=Path(rule_str),
                    policy_doctrine=Path(policy_str),
                ),
            )
        return result

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
            msg = str(e)
            logger.warning(msg)
            result = Result.failure(msg)
        return result

    # ── Paths (lint targets, required) ────────────────────────────────────

    def _build_paths(self, a_toml: dict[str, Any]) -> Result[PathsConfig]:
        """Build paths config from toml > env."""
        b_continue = True
        result: Result[PathsConfig] = Result.failure("unreachable")
        data = a_toml.get("paths", {})

        include_str = os.environ.get(f"{_ENV_PREFIX}PATHS_INCLUDE")
        exclude_str = os.environ.get(f"{_ENV_PREFIX}PATHS_EXCLUDE")
        extensions_str = os.environ.get(f"{_ENV_PREFIX}PATHS_EXTENSIONS")

        include_raw = include_str.split(",") if include_str else data.get("include")
        exclude_raw = exclude_str.split(",") if exclude_str else data.get("exclude")
        extensions_raw = (
            extensions_str.split(",") if extensions_str else data.get("extensions")
        )

        if b_continue and not include_raw:
            b_continue = False
            msg = (
                "paths.include required. Set [tool.selma.paths.include] or "
                + "SELMA_PATHS_INCLUDE."
            )
            logger.warning(msg)
            msg = (
                "paths.include required. Set [tool.selma.paths.include] or "
                + "SELMA_PATHS_INCLUDE."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not exclude_raw:
            b_continue = False
            msg = (
                "paths.exclude required. Set [tool.selma.paths.exclude] or "
                + "SELMA_PATHS_EXCLUDE."
            )
            logger.warning(msg)
            msg = (
                "paths.exclude required. Set [tool.selma.paths.exclude] or "
                + "SELMA_PATHS_EXCLUDE."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not extensions_raw:
            b_continue = False
            msg = (
                "paths.extensions required. Set [tool.selma.paths.extensions] or "
                + "SELMA_PATHS_EXTENSIONS."
            )
            logger.warning(msg)
            msg = (
                "paths.extensions required. Set [tool.selma.paths.extensions] or "
                + "SELMA_PATHS_EXTENSIONS."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = Result.success(
                PathsConfig(
                    include=tuple(include_raw),
                    exclude=tuple(exclude_raw),
                    extensions=tuple(extensions_raw),
                ),
            )
        return result

    # ── Output (required) ─────────────────────────────────────────────────

    def _build_output(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[OutputConfig]:
        """Build output config from toml > env > cli."""
        b_continue = True
        result: Result[OutputConfig] = Result.failure("unreachable")
        toml_data = a_toml.get("output", {})

        env_fmt = os.environ.get(f"{_ENV_PREFIX}OUTPUT_FORMAT")
        env_guide = os.environ.get(f"{_ENV_PREFIX}OUTPUT_GUIDE")
        env_file = os.environ.get(f"{_ENV_PREFIX}OUTPUT_FILE")
        env_color = os.environ.get(f"{_ENV_PREFIX}OUTPUT_COLOR")

        fmt = env_fmt or toml_data.get("format")
        guide = False
        file = env_file or toml_data.get("file")
        color = False

        if b_continue and not fmt:
            b_continue = False
            msg = (
                "output.format required. Set [tool.selma.output.format] or "
                + "SELMA_OUTPUT_FORMAT."
            )
            logger.warning(msg)
            msg = (
                "output.format required. Set [tool.selma.output.format] or "
                + "SELMA_OUTPUT_FORMAT."
            )
            logger.warning(msg)
            result = Result.failure(msg)

        guide_str = env_guide or toml_data.get("guide")
        if b_continue and guide_str is None:
            b_continue = False
            msg = (
                "output.guide required. Set [tool.selma.output.guide] or "
                + "SELMA_OUTPUT_GUIDE."
            )
            logger.warning(msg)
            msg = (
                "output.guide required. Set [tool.selma.output.guide] or "
                + "SELMA_OUTPUT_GUIDE."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            guide = str(guide_str).lower() in ("true", "1", "yes")

        color_str = env_color or toml_data.get("color")
        if b_continue and color_str is None:
            b_continue = False
            msg = (
                "output.color required. Set [tool.selma.output.color] or "
                + "SELMA_OUTPUT_COLOR."
            )
            logger.warning(msg)
            msg = (
                "output.color required. Set [tool.selma.output.color] or "
                + "SELMA_OUTPUT_COLOR."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            color = str(color_str).lower() in ("true", "1", "yes")

        if b_continue and a_cli_args:
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

        if b_continue:
            result = Result.success(
                OutputConfig(format=fmt, guide=guide, file=file, color=color)
            )
        return result

    # ── Execution (required) ──────────────────────────────────────────────

    def _build_execution(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[ExecutionConfig]:
        """Build execution config from toml > env > cli."""
        b_continue = True
        result: Result[ExecutionConfig] = Result.failure("unreachable")
        toml_data = a_toml.get("execution", {})

        env_skip_tools = os.environ.get(f"{_ENV_PREFIX}EXECUTION_SKIP_TOOLS")
        env_skip_ast = os.environ.get(f"{_ENV_PREFIX}EXECUTION_SKIP_AST")
        env_only = os.environ.get(f"{_ENV_PREFIX}EXECUTION_ONLY")
        env_workers = os.environ.get(f"{_ENV_PREFIX}EXECUTION_MAX_WORKERS")
        env_timeout = os.environ.get(f"{_ENV_PREFIX}EXECUTION_FILE_TIMEOUT")

        skip_tools = False
        skip_ast = False
        only = env_only or toml_data.get("only")
        if only == "":
            only = None
        max_workers_str = env_workers or toml_data.get("max_workers")
        file_timeout_str = env_timeout or toml_data.get("file_timeout")

        skip_tools_str = env_skip_tools or toml_data.get("skip_tools")
        if b_continue and skip_tools_str is None:
            b_continue = False
            msg = (
                "execution.skip_tools required. Set "
                + "[tool.selma.execution.skip_tools] or SELMA_EXECUTION_SKIP_TOOLS."
            )
            logger.warning(msg)
            msg = (
                "execution.skip_tools required. Set "
                + "[tool.selma.execution.skip_tools] or SELMA_EXECUTION_SKIP_TOOLS."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            skip_tools = str(skip_tools_str).lower() in ("true", "1", "yes")

        skip_ast_str = env_skip_ast or toml_data.get("skip_ast")
        if b_continue and skip_ast_str is None:
            b_continue = False
            msg = (
                "execution.skip_ast required. Set "
                + "[tool.selma.execution.skip_ast] or SELMA_EXECUTION_SKIP_AST."
            )
            logger.warning(msg)
            msg = (
                "execution.skip_ast required. Set "
                + "[tool.selma.execution.skip_ast] or SELMA_EXECUTION_SKIP_AST."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            skip_ast = str(skip_ast_str).lower() in ("true", "1", "yes")

        if b_continue and max_workers_str is None:
            b_continue = False
            msg = (
                "execution.max_workers required. Set "
                + "[tool.selma.execution.max_workers] or SELMA_EXECUTION_MAX_WORKERS."
            )
            logger.warning(msg)
            msg = (
                "execution.max_workers required. Set "
                + "[tool.selma.execution.max_workers] or SELMA_EXECUTION_MAX_WORKERS."
            )
            logger.warning(msg)
            result = Result.failure(msg)

        if b_continue and file_timeout_str is None:
            b_continue = False
            msg = (
                "execution.file_timeout required. Set "
                + "[tool.selma.execution.file_timeout] or SELMA_EXECUTION_FILE_TIMEOUT."
            )
            logger.warning(msg)
            msg = (
                "execution.file_timeout required. Set "
                + "[tool.selma.execution.file_timeout] or SELMA_EXECUTION_FILE_TIMEOUT."
            )
            logger.warning(msg)
            result = Result.failure(msg)

        if b_continue and a_cli_args:
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

        if b_continue and max_workers_str is not None and file_timeout_str is not None:
            result = Result.success(
                ExecutionConfig(
                    skip_tools=skip_tools,
                    skip_ast=skip_ast,
                    only=only,
                    max_workers=int(max_workers_str),
                    file_timeout=int(file_timeout_str),
                ),
            )
        return result

    # ── Rules filter (required) ───────────────────────────────────────────

    def _build_rules_filter(
        self,
        a_toml: dict[str, Any],
        a_cli_args: dict[str, Any] | None,
    ) -> Result[RulesFilterConfig]:
        """Build rules filter from toml > env > cli."""
        b_continue = True
        result: Result[RulesFilterConfig] = Result.failure("unreachable")
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

        if b_continue and disabled_raw is None:
            b_continue = False
            msg = (
                "rules.disabled required (use [] for none). Set "
                + "[tool.selma.rules.disabled] or SELMA_RULES_DISABLED."
            )
            logger.warning(msg)
            msg = (
                "rules.disabled required (use [] for none). Set "
                + "[tool.selma.rules.disabled] or SELMA_RULES_DISABLED."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and codes_raw is None:
            b_continue = False
            msg = (
                "rules.codes required (use [] for all). Set "
                + "[tool.selma.rules.codes] or SELMA_RULES_CODES."
            )
            logger.warning(msg)
            msg = (
                "rules.codes required (use [] for all). Set "
                + "[tool.selma.rules.codes] or SELMA_RULES_CODES."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and exclude_raw is None:
            b_continue = False
            msg = (
                "rules.exclude_codes required (use [] for none). Set "
                + "[tool.selma.rules.exclude_codes] or SELMA_RULES_EXCLUDE_CODES."
            )
            logger.warning(msg)
            msg = (
                "rules.exclude_codes required (use [] for none). Set "
                + "[tool.selma.rules.exclude_codes] or SELMA_RULES_EXCLUDE_CODES."
            )
            logger.warning(msg)
            result = Result.failure(msg)

        if (
            b_continue
            and disabled_raw is not None
            and codes_raw is not None
            and exclude_raw is not None
        ):
            disabled = tuple(str(c).strip() for c in disabled_raw if str(c).strip())
            codes = tuple(str(c).strip() for c in codes_raw if str(c).strip())
            exclude_codes = tuple(str(c).strip() for c in exclude_raw if str(c).strip())

            if a_cli_args:
                cli_codes = a_cli_args.get("codes")
                if cli_codes:
                    codes = tuple(str(c) for c in cli_codes)
                cli_exclude = a_cli_args.get("exclude_codes")
                if cli_exclude:
                    exclude_codes = tuple(str(c) for c in cli_exclude)
                cli_disable = a_cli_args.get("disable")
                if cli_disable:
                    disabled = tuple(str(c) for c in cli_disable)

            result = Result.success(
                RulesFilterConfig(
                    disabled=disabled,
                    codes=codes,
                    exclude_codes=exclude_codes,
                ),
            )
        return result

    # ── Tools (required) ──────────────────────────────────────────────────

    def _build_tools(self, a_toml: dict[str, Any]) -> Result[ToolsConfig]:
        """Build tools config from toml."""
        b_continue = True
        result: Result[ToolsConfig] = Result.failure("unreachable")
        data = a_toml.get("tools", {})

        ruff_data = data.get("ruff")
        pylint_data = data.get("pylint")
        pyright_data = data.get("pyright")

        ruff_result: Result[ToolConfig] = Result.failure("unreachable")
        pylint_result: Result[ToolConfig] = Result.failure("unreachable")
        pyright_result: Result[ToolConfig] = Result.failure("unreachable")

        if b_continue and not ruff_data:
            b_continue = False
            msg = "tools.ruff required. Set [tool.selma.tools.ruff] in pyproject.toml."
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not pylint_data:
            b_continue = False
            msg = "tools.pylint required. Set [tool.selma.tools.pylint] in pyproject.toml."
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not pyright_data:
            b_continue = False
            msg = "tools.pyright required. Set [tool.selma.tools.pyright] in pyproject.toml."
            logger.warning(msg)
            result = Result.failure(msg)

        if b_continue:
            ruff_result = self._build_tool_config("ruff", ruff_data)
            if ruff_result.is_failure():
                b_continue = False
                msg = ruff_result.message
                logger.warning(msg)
                result = Result.failure(msg)
        if b_continue:
            pylint_result = self._build_tool_config("pylint", pylint_data)
            if pylint_result.is_failure():
                b_continue = False
                msg = pylint_result.message
                logger.warning(msg)
                result = Result.failure(msg)
        if b_continue:
            pyright_result = self._build_tool_config("pyright", pyright_data)
            if pyright_result.is_failure():
                b_continue = False
                msg = pyright_result.message
                logger.warning(msg)
                result = Result.failure(msg)

        if b_continue:
            result = Result.success(
                ToolsConfig(
                    ruff=ruff_result.unwrap(),
                    pylint=pylint_result.unwrap(),
                    pyright=pyright_result.unwrap(),
                ),
            )
        return result

    def _build_tool_config(
        self,
        a_name: str,
        a_data: dict[str, Any],
    ) -> Result[ToolConfig]:
        """Build a single tool config from toml data."""
        b_continue = True
        result: Result[ToolConfig] = Result.failure("unreachable")
        enabled = a_data.get("enabled")
        binary = a_data.get("binary")
        args_raw = a_data.get("args")
        fail_under = a_data.get("fail_under")

        if b_continue and enabled is None:
            b_continue = False
            msg = f"tools.{a_name}.enabled required."
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not binary:
            b_continue = False
            msg = f"tools.{a_name}.binary required."
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and args_raw is None:
            b_continue = False
            msg = f"tools.{a_name}.args required (use [] for none)."
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and fail_under is None:
            b_continue = False
            msg = f"tools.{a_name}.fail_under required."
            logger.warning(msg)
            result = Result.failure(msg)
        if (
            b_continue
            and enabled is not None
            and binary is not None
            and args_raw is not None
            and fail_under is not None
        ):
            args_list: list[object]
            if isinstance(args_raw, list):
                args_list = cast("list[object]", args_raw)
            elif isinstance(args_raw, tuple):
                args_list = list(cast("tuple[object, ...]", args_raw))
            else:
                args_list = [cast("object", args_raw)]
            result = Result.success(
                ToolConfig(
                    enabled=bool(enabled),
                    binary=str(binary),
                    args=tuple(str(item) for item in args_list),
                    rcfile=a_data.get("rcfile"),
                    fail_under=int(fail_under),
                ),
            )
        return result

    # ── Logging (required) ────────────────────────────────────────────────

    def _build_logging(self, a_toml: dict[str, Any]) -> Result[LoggingConfig]:
        """Build logging config from toml > env."""
        b_continue = True
        result: Result[LoggingConfig] = Result.failure("unreachable")
        toml_data = a_toml.get("logging", {})

        env_level = os.environ.get(f"{_ENV_PREFIX}LOGGING_LEVEL")
        env_logger_name = os.environ.get(f"{_ENV_PREFIX}LOGGING_LOGGER_NAME")
        env_diag_fmt = os.environ.get(f"{_ENV_PREFIX}LOGGING_DIAGNOSTIC_FORMAT")
        env_ops_fmt = os.environ.get(f"{_ENV_PREFIX}LOGGING_OPERATIONAL_FORMAT")
        env_file = os.environ.get(f"{_ENV_PREFIX}LOGGING_FILE")
        env_enabled = os.environ.get(f"{_ENV_PREFIX}LOGGING_ENABLED")
        env_log_dir = os.environ.get(f"{_ENV_PREFIX}LOGGING_LOG_DIR")
        env_max_bytes = os.environ.get(f"{_ENV_PREFIX}LOGGING_MAX_BYTES")
        env_backup_count = os.environ.get(f"{_ENV_PREFIX}LOGGING_BACKUP_COUNT")

        level = env_level or toml_data.get("level")
        logger_name = env_logger_name or toml_data.get("logger_name")
        diag_fmt = env_diag_fmt or toml_data.get("diagnostic_format")
        ops_fmt = env_ops_fmt or toml_data.get("operational_format")
        file = env_file or toml_data.get("file")
        enabled = False
        log_dir = env_log_dir if env_log_dir is not None else toml_data.get("log_dir")
        if log_dir == "":
            log_dir = None
        max_bytes_raw = env_max_bytes or toml_data.get("max_bytes")
        backup_count_raw = env_backup_count or toml_data.get("backup_count")

        if b_continue and not level:
            b_continue = False
            msg = (
                "logging.level required. Set [tool.selma.logging.level] or "
                + "SELMA_LOGGING_LEVEL."
            )
            logger.warning(msg)
            msg = (
                "logging.level required. Set [tool.selma.logging.level] or "
                + "SELMA_LOGGING_LEVEL."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not logger_name:
            b_continue = False
            msg = (
                "logging.logger_name required. Set "
                + "[tool.selma.logging.logger_name] or SELMA_LOGGING_LOGGER_NAME."
            )
            logger.warning(msg)
            msg = (
                "logging.logger_name required. Set "
                + "[tool.selma.logging.logger_name] or SELMA_LOGGING_LOGGER_NAME."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not diag_fmt:
            b_continue = False
            msg = (
                "logging.diagnostic_format required. Set "
                + "[tool.selma.logging.diagnostic_format] or SELMA_LOGGING_DIAGNOSTIC_FORMAT."
            )
            logger.warning(msg)
            msg = (
                "logging.diagnostic_format required. Set "
                + "[tool.selma.logging.diagnostic_format] or SELMA_LOGGING_DIAGNOSTIC_FORMAT."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and not ops_fmt:
            b_continue = False
            msg = (
                "logging.operational_format required. Set "
                + "[tool.selma.logging.operational_format] or SELMA_LOGGING_OPERATIONAL_FORMAT."
            )
            logger.warning(msg)
            msg = (
                "logging.operational_format required. Set "
                + "[tool.selma.logging.operational_format] or SELMA_LOGGING_OPERATIONAL_FORMAT."
            )
            logger.warning(msg)
            result = Result.failure(msg)

        enabled_raw = env_enabled or toml_data.get("enabled")
        if b_continue and enabled_raw is None:
            b_continue = False
            msg = (
                "logging.enabled required. Set "
                + "[tool.selma.logging.enabled] or SELMA_LOGGING_ENABLED."
            )
            logger.warning(msg)
            msg = (
                "logging.enabled required. Set "
                + "[tool.selma.logging.enabled] or SELMA_LOGGING_ENABLED."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            enabled = str(enabled_raw).lower() in ("true", "1", "yes")

        if b_continue and max_bytes_raw is None:
            b_continue = False
            msg = (
                "logging.max_bytes required. Set "
                + "[tool.selma.logging.max_bytes] or SELMA_LOGGING_MAX_BYTES."
            )
            logger.warning(msg)
            msg = (
                "logging.max_bytes required. Set "
                + "[tool.selma.logging.max_bytes] or SELMA_LOGGING_MAX_BYTES."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and backup_count_raw is None:
            b_continue = False
            msg = (
                "logging.backup_count required. Set "
                + "[tool.selma.logging.backup_count] or SELMA_LOGGING_BACKUP_COUNT."
            )
            logger.warning(msg)
            msg = (
                "logging.backup_count required. Set "
                + "[tool.selma.logging.backup_count] or SELMA_LOGGING_BACKUP_COUNT."
            )
            logger.warning(msg)
            result = Result.failure(msg)
        if (
            b_continue
            and level is not None
            and logger_name is not None
            and diag_fmt is not None
            and ops_fmt is not None
            and max_bytes_raw is not None
            and backup_count_raw is not None
        ):
            result = Result.success(
                LoggingConfig(
                    level=str(level),
                    logger_name=str(logger_name),
                    diagnostic_format=str(diag_fmt),
                    operational_format=str(ops_fmt),
                    file=file,
                    enabled=enabled,
                    log_dir=log_dir,
                    max_bytes=int(max_bytes_raw),
                    backup_count=int(backup_count_raw),
                )
            )
        return result
