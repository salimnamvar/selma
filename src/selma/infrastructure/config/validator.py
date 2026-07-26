"""Configuration validator — validates infrastructure config values at load time.

Rule validation is handled by schema/validate_rules.py (JSON Schema).
This validator handles infrastructure config only.
"""

from __future__ import annotations

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.models import SelmaConfig

VALID_FORMATS = frozenset({"default", "json", "gcc", "guidance"})
VALID_CHECKS = frozenset(
    {
        "ruff-check",
        "ruff-format",
        "pylint",
        "pyright",
        "ast",
    }
)


class ConfigValidator:
    """Validate configuration values."""

    def validate(self, a_config: SelmaConfig) -> Result[SelmaConfig]:
        """Validate all configuration values.

        Preconditions:
            - a_config is a loaded SelmaConfig instance.

        Postconditions:
            Returns Result.success with validated config, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on invalid config values.
        """
        errors: list[str] = []

        self._validate_output(a_config, errors)
        self._validate_execution(a_config, errors)
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
        if a_config.output.format not in VALID_FORMATS:
            a_errors.append(f"Invalid output format: {a_config.output.format}")

    def _validate_execution(
        self,
        a_config: SelmaConfig,
        a_errors: list[str],
    ) -> None:
        """Validate execution configuration."""
        if (
            a_config.execution.only is not None
            and a_config.execution.only != ""
            and a_config.execution.only not in VALID_CHECKS
        ):
            a_errors.append(f"Invalid check: {a_config.execution.only}")
        if a_config.execution.max_workers < 1:
            a_errors.append("max_workers must be >= 1")
        if a_config.execution.file_timeout < 1:
            a_errors.append("file_timeout must be >= 1")

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
        for name, tool in tools:
            if not tool.binary:
                a_errors.append(f"Tool '{name}' has empty binary path")

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
        if a_config.logging.level not in valid_levels:
            a_errors.append(f"Invalid log level: {a_config.logging.level}")
