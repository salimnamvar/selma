"""Logging initialization — configures stdlib logging for Selma.

Project rule
------------
Never instantiate, attach, or reconfigure handlers outside this module.
Business code must only call ``logging.getLogger(__name__)`` and emit records.
All wiring (handlers, formatters, filters, QueueListener) lives here.

Invariants
----------
1. Only the **root** logger owns output handlers.
2. Named loggers set level, clear handlers, and **propagate** to root.
3. ``configure_logging()`` is called **once** per process at startup.
   A second call with ``enabled=True`` would start another
   QueueListener without stopping the first.

Formatting policy
-----------------
Logging format is selected internally by severity:

    Diagnostic (< INFO):  LEVEL WHEN WHERE RESOURCE : MESSAGE
    Operational (>= INFO): LEVEL WHEN RESOURCE : MESSAGE

WHERE = filename:lineno (diagnostic only)
WHEN = UTC ISO-8601 timestamp
RESOURCE = optional extra field (e.g. ``resource="model_id=bert"``)

File logging
------------
When ``LoggingConfig.log_dir`` is set, logs are written to:
    <log_dir>/selma.log

Files rotate at ``max_bytes`` with ``backup_count`` backups.
Log directory is created automatically if it does not exist.
"""

from __future__ import annotations

from datetime import UTC as _UTC
from datetime import datetime
import logging
import logging.config
import logging.handlers
from pathlib import Path
import queue
from typing import Any

from selma.domain.value_objects.result import INVALID_RESULT
from selma.domain.value_objects.result import Result
from selma.infrastructure.config.models import LoggingConfig

_logger = logging.getLogger(__name__)


def _format_utc_timestamp(a_epoch_seconds: float) -> Result[str]:
    """Format Unix epoch seconds as canonical UTC ISO-8601 (microseconds + Z).

    Args:
        a_epoch_seconds: Unix epoch timestamp.

    Returns:
        Result.success with formatted string like ``2026-07-18T23:45:12.345678Z``.
    """
    result: Result[str] = INVALID_RESULT
    b_continue: bool = True
    if b_continue:
        dt: datetime = datetime.fromtimestamp(a_epoch_seconds, tz=_UTC)
        result = Result.success(
            dt.astimezone(_UTC)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
    return result


class IsoUtcFormatter(logging.Formatter):
    """UTC ISO-8601 timestamp formatter."""

    def _format_time(
        self,
        record: logging.LogRecord,
        datefmt: str | None = None,
    ) -> str:
        return _format_utc_timestamp(record.created).value or ""

    formatTime = _format_time  # noqa: N815 — stdlib Formatter protocol


class ResourceFilter(logging.Filter):
    """Inject format-safe ``resource`` attribute; always admit the record."""

    def filter(self, record: logging.LogRecord) -> bool:
        resource = getattr(record, "resource", None)
        if resource:
            record.resource = f" {resource}"
        else:
            record.resource = ""
        return True


class DiagnosticLevelFilter(logging.Filter):
    """Admit Diagnostic (< INFO) records only."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.INFO


def _build_file_handler(a_config: LoggingConfig) -> Result[dict[str, Any]]:
    """Build file handler dict if log_dir is configured.

    Args:
        a_config: Validated logging configuration.

    Returns:
        Result.success with handler dict for RotatingFileHandler, or Result.failure if log_dir is not set.
    """
    result: Result[dict[str, Any]] = INVALID_RESULT
    b_continue: bool = True

    if b_continue and a_config.log_dir is None:
        logger.warning("No log_dir configured")
        result = Result.failure("No log_dir configured")
        b_continue = False

    if b_continue and a_config.log_dir is not None:
        log_dir: Path = Path(a_config.log_dir).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file: Path = log_dir / "selma.log"
        result = Result.success(
            {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "NOTSET",
                "formatter": "file",
                "filters": ["run_context", "resource"],
                "filename": str(log_file),
                "maxBytes": a_config.max_bytes,
                "backupCount": a_config.backup_count,
                "encoding": "utf-8",
            },
            "File handler built",
        )

    return result


def _build_filters() -> Result[dict[str, Any]]:
    """Build filter definitions for dictConfig.

    Returns:
        Result.success with dictionary of filter configurations.
    """
    result: Result[dict[str, Any]] = INVALID_RESULT
    b_continue: bool = True
    if b_continue:
        result = Result.success(
            {
                "resource": {
                    "()": f"{__name__}.ResourceFilter",
                },
                "diagnostic_level": {
                    "()": f"{__name__}.DiagnosticLevelFilter",
                },
                "run_context": {
                    "()": "selma.infrastructure.bootstrap.logging_filters.RunContextFilter",
                },
            },
            "Filters built",
        )
    return result


def _build_formatters(a_config: LoggingConfig) -> Result[dict[str, Any]]:
    """Build formatter definitions for dictConfig.

    Args:
        a_config: Logging configuration with format strings.

    Returns:
        Result.success with dictionary of formatter configurations.
    """
    result: Result[dict[str, Any]] = INVALID_RESULT
    b_continue: bool = True
    if b_continue:
        result = Result.success(
            {
                "diagnostic": {
                    "()": f"{__name__}.IsoUtcFormatter",
                    "format": a_config.diagnostic_format,
                },
                "operational": {
                    "()": f"{__name__}.IsoUtcFormatter",
                    "format": a_config.operational_format,
                },
                "file": {
                    "()": f"{__name__}.IsoUtcFormatter",
                    "format": a_config.diagnostic_format,
                },
            },
            "Formatters built",
        )
    return result


def _build_loggers(
    a_level: str,
    a_logger_names: tuple[str, ...],
) -> Result[dict[str, Any]]:
    """Build logger definitions for dictConfig.

    Args:
        a_level: Logging level for named loggers.
        a_logger_names: Logger names that propagate to root.

    Returns:
        Result.success with dictionary of logger configurations.
    """
    result: Result[dict[str, Any]] = INVALID_RESULT
    b_continue: bool = True
    if b_continue:
        result = Result.success(
            {
                name: {
                    "level": a_level,
                    "handlers": [],
                    "propagate": True,
                }
                for name in a_logger_names
            },
            "Loggers built",
        )
    return result


def _build_logging_config(a_config: LoggingConfig) -> Result[dict[str, Any]]:
    """Build dictConfig: named loggers propagate to root; root owns handlers.

    Handlers:
        console_debug: diagnostic (< INFO) to stderr
        console_ops: operational (>= INFO) to stderr
        file: all levels to rotating file (if log_dir is set)

    Args:
        a_config: Validated logging configuration.

    Returns:
        Result.success with dictionary suitable for logging.config.dictConfig.
    """
    result: Result[dict[str, Any]] = INVALID_RESULT
    b_continue: bool = True

    level: str = a_config.level

    handlers: dict[str, dict[str, Any]] = {
        "console_debug": {
            "class": "logging.StreamHandler",
            "level": "NOTSET",
            "formatter": "diagnostic",
            "filters": ["run_context", "diagnostic_level", "resource"],
            "stream": "ext://sys.stderr",
        },
        "console_ops": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "operational",
            "filters": ["run_context", "resource"],
            "stream": "ext://sys.stderr",
        },
    }

    root_handlers: list[str] = ["console_debug", "console_ops"]

    file_handler_result: Result[dict[str, Any]] = _build_file_handler(a_config)
    if file_handler_result.is_success() and file_handler_result.value is not None:
        handlers["file"] = file_handler_result.value
        root_handlers.append("file")

    filters_result: Result[dict[str, Any]] = INVALID_RESULT
    formatters_result: Result[dict[str, Any]] = INVALID_RESULT
    loggers_result: Result[dict[str, Any]] = INVALID_RESULT

    logger_names: tuple[str, ...] = (a_config.logger_name,)

    if b_continue:
        filters_result = _build_filters()
        formatters_result = _build_formatters(a_config)
        loggers_result = _build_loggers(level, logger_names)
        if b_continue and not (
            filters_result.is_success()
            and formatters_result.is_success()
            and loggers_result.is_success()
        ):
            logger.warning("Failed to build logging sub-configs")
            result = Result.failure("Failed to build logging sub-configs")
            b_continue = False

    if b_continue and (
        filters_result.value is None
        or formatters_result.value is None
        or loggers_result.value is None
    ):
        logger.warning("Failed to build logging sub-configs")
        result = Result.failure("Failed to build logging sub-configs")
        b_continue = False

    if b_continue:
        result = Result.success(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "filters": filters_result.value,
                "formatters": formatters_result.value,
                "handlers": handlers,
                "loggers": loggers_result.value,
                "root": {
                    "level": "WARNING",
                    "handlers": root_handlers,
                },
            },
            "Logging config built",
        )

    return result


def _replace_handlers(
    a_logger: logging.Logger, a_handler: logging.Handler
) -> Result[None]:
    """Replace all handlers on *a_logger* with *a_handler*.

    Args:
        a_logger: Logger to modify.
        a_handler: Handler to install.

    Returns:
        Result.success with None.
    """
    result: Result[None] = INVALID_RESULT
    b_continue: bool = True
    if b_continue:
        a_logger.handlers.clear()
        a_logger.addHandler(a_handler)
        result = Result.success(None, "Handlers replaced")
    return result


def _enable_async_logging() -> Result[logging.handlers.QueueListener]:
    """Route root handlers through QueueHandler → QueueListener for non-blocking I/O.

    Returns:
        Result.success with running QueueListener, or Result.failure if no handlers found.
    """
    result: Result[logging.handlers.QueueListener] = INVALID_RESULT
    b_continue: bool = True

    root: logging.Logger = logging.getLogger()
    targets: list[logging.Handler] = [
        handler
        for handler in root.handlers
        if not isinstance(handler, logging.handlers.QueueHandler)
    ]
    if b_continue and not targets:
        msg = "Cannot enable async logging: root logger has no handlers"
        logger.warning(msg)
        result = Result.failure(msg)
        b_continue = False

    if b_continue:
        log_queue: queue.SimpleQueue[logging.LogRecord] = queue.SimpleQueue()
        queue_handler: logging.handlers.QueueHandler = logging.handlers.QueueHandler(
            log_queue
        )
        _replace_handlers(root, queue_handler)

        listener: logging.handlers.QueueListener = logging.handlers.QueueListener(
            log_queue,
            *targets,
            respect_handler_level=True,
        )
        listener.start()
        result = Result.success(listener, "Async logging enabled")

    return result


def configure_logging(
    a_config: LoggingConfig,
) -> Result[logging.handlers.QueueListener]:
    """Apply dictConfig + captureWarnings once at process startup.

    Returns a running ``QueueListener`` when async logging is enabled, or Result.failure otherwise.

    Args:
        a_config: Logging configuration. Required — no defaults.

    Returns:
        Result.success with running QueueListener if enabled, Result.failure otherwise.
    """
    result: Result[logging.handlers.QueueListener] = INVALID_RESULT
    b_continue: bool = True

    config: LoggingConfig = a_config

    logging_config_result: Result[dict[str, Any]] = INVALID_RESULT

    if b_continue:
        logging_config_result = _build_logging_config(config)
        if b_continue and not logging_config_result.is_success():
            result = Result.failure(logging_config_result.message)
            b_continue = False

    if b_continue and logging_config_result.value is None:
        msg = logging_config_result.message or "Logging config missing value"
        logger.warning(msg)
        result = Result.failure(msg)
        b_continue = False

    if b_continue and logging_config_result.value is not None:
        logging.config.dictConfig(logging_config_result.value)
        logging.captureWarnings(True)  # noqa: FBT003 — stdlib API, positional required

    if b_continue:
        if config.enabled:
            async_result: Result[logging.handlers.QueueListener] = (
                _enable_async_logging()
            )
            if async_result.is_success():
                result = async_result
            else:
                _logger.error(
                    "Failed to enable async logging: %s", async_result.message
                )
                result = async_result
        else:
            logger.warning("Async logging not enabled")
            result = Result.failure("Async logging not enabled")

    return result
