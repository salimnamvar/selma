"""Configuration validator — validates all config values at load time.

Single responsibility: validate config, never mutate it.
"""

from __future__ import annotations

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.models import SelmaConfig

VALID_FORMATS = frozenset({"default", "json", "gcc", "guidance"})
VALID_SEVERITIES = frozenset(
    {
        "critical",
        "high",
        "medium",
        "low",
        "warning",
        "info",
    }
)
VALID_CHECKS = frozenset(
    {
        "ruff-check",
        "ruff-format",
        "pylint",
        "pyright",
        "ast",
    }
)
VALID_PRIORITIES = frozenset(
    {
        "constitutional",
        "statutory",
        "regulatory",
        "operational",
        "advisory",
    }
)


class ConfigValidator:
    """Validate configuration values."""

    def validate(self, a_config: SelmaConfig) -> Result[SelmaConfig]:
        """Validate all configuration values.

        Preconditions:
            - a_config is a loaded SelmaConfig instance.

        Postconditions:
            - Returns Result.success with validated config, or
              Result.failure with error message.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on invalid config values.
        """
        errors: list[str] = []

        self._validate_output(a_config, errors)
        self._validate_execution(a_config, errors)
        self._validate_rules(a_config, errors)
        self._validate_tools(a_config, errors)
        self._validate_logging(a_config, errors)

        b_continue = True
        result: Result[SelmaConfig] = Result.failure("unreachable")
        if b_continue and errors:
            b_continue = False
            result = Result.failure("; ".join(errors))
        if b_continue:
            result = Result.success(a_config)
        return result

    def _validate_output(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate output configuration."""
        b_continue = True
        if b_continue and a_config.output.format not in VALID_FORMATS:
            b_continue = False
            a_errors.append(f"Invalid output format: {a_config.output.format}")

    def _validate_execution(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate execution configuration."""
        b_continue = True
        if (
            b_continue
            and a_config.execution.only is not None
            and a_config.execution.only != ""
            and a_config.execution.only not in VALID_CHECKS
        ):
            b_continue = False
            a_errors.append(f"Invalid check: {a_config.execution.only}")
        b_continue = True
        if b_continue and a_config.execution.max_workers < 1:
            b_continue = False
            a_errors.append("max_workers must be >= 1")
        b_continue = True
        if b_continue and a_config.execution.file_timeout < 1:
            b_continue = False
            a_errors.append("file_timeout must be >= 1")

    def _validate_rules(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate rule configurations."""
        rule_configs = [
            ("SC001", a_config.rules.sc001),
            ("SC002", a_config.rules.sc002),
            ("SC003", a_config.rules.sc003),
            ("SC004", a_config.rules.sc004),
            ("SC005", a_config.rules.sc005),
            ("SC007", a_config.rules.sc007),
            ("SC010", a_config.rules.sc010),
            ("SC011", a_config.rules.sc011),
            ("SC013", a_config.rules.sc013),
            ("SC022", a_config.rules.sc022),
            ("SC024", a_config.rules.sc024),
            ("SC025", a_config.rules.sc025),
            ("SC031", a_config.rules.sc031),
            ("SC033", a_config.rules.sc033),
            ("SC041", a_config.rules.sc041),
            ("SC042", a_config.rules.sc042),
            ("SC052", a_config.rules.sc052),
            ("SC060", a_config.rules.sc060),
            ("SC061", a_config.rules.sc061),
            ("SC062", a_config.rules.sc062),
            ("SC065", a_config.rules.sc065),
            ("SC070", a_config.rules.sc070),
            ("SC071", a_config.rules.sc071),
            ("SC080", a_config.rules.sc080),
            ("SC090", a_config.rules.sc090),
            ("SC092", a_config.rules.sc092),
            ("SC100", a_config.rules.sc100),
            ("SC101", a_config.rules.sc101),
            ("SC104", a_config.rules.sc104),
            ("SC114", a_config.rules.sc114),
            ("SC115", a_config.rules.sc115),
        ]
        for a_name, a_rc in rule_configs:
            self._validate_rule_severity(a_name, a_rc.severity, a_errors)

    def _validate_rule_severity(
        self,
        a_name: str,
        a_severity: str,
        a_errors: list[str],
    ) -> None:
        """Validate a single rule's severity."""
        b_continue = True
        if b_continue and a_severity not in VALID_SEVERITIES:
            b_continue = False
            a_errors.append(f"{a_name}: invalid severity '{a_severity}'")

    def _validate_tools(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate tool configurations."""
        tools = [
            ("ruff", a_config.tools.ruff),
            ("pylint", a_config.tools.pylint),
            ("pyright", a_config.tools.pyright),
        ]
        for a_name, a_tool in tools:
            self._validate_tool_binary(a_name, a_tool.binary, a_errors)

    def _validate_tool_binary(
        self,
        a_name: str,
        a_binary: str,
        a_errors: list[str],
    ) -> None:
        """Validate a tool has a binary name when enabled."""
        b_continue = True
        if b_continue and not a_binary:
            b_continue = False
            a_errors.append(f"Tool '{a_name}' has empty binary path")

    def _validate_logging(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate logging configuration."""
        valid_levels = frozenset(
            {
                "DEBUG",
                "INFO",
                "WARNING",
                "ERROR",
                "CRITICAL",
            }
        )
        b_continue = True
        if b_continue and a_config.logging.level not in valid_levels:
            b_continue = False
            a_errors.append(f"Invalid log level: {a_config.logging.level}")
