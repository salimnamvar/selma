"""Application lifespan — startup/shutdown lifecycle orchestration.

Provides both sync and async context managers:
- Sync (for CLI): ``with lifespan(config): ...``
- Async (for future ASGI): ``async with async_lifespan(config): ...``
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from collections.abc import Generator
from contextlib import asynccontextmanager
from contextlib import contextmanager
import logging
import logging.handlers

from selma.domain.value_objects.result import Result
from selma.infrastructure.bootstrap.logging import configure_logging
from selma.infrastructure.config.models import LoggingConfig

_logger = logging.getLogger(__name__)


@contextmanager
def lifespan(
    a_config: LoggingConfig,
) -> Generator[None]:
    """Sync lifespan for CLI: configure logging on startup, stop listener on shutdown.

    Args:
        a_config: Logging configuration.

    Yields:
        None — application is alive during yield.
    """
    listener: logging.handlers.QueueListener | None = None

    logging_result: Result[logging.handlers.QueueListener] = configure_logging(a_config)
    _logger.debug("Logging configured at level %s", a_config.level.upper())
    if logging_result.is_success():
        listener = logging_result.value

    _logger.info("Selma starting")

    try:
        yield
    finally:
        _logger.info("Selma stopped")
        if listener is not None:
            listener.stop()


@asynccontextmanager
async def async_lifespan(
    a_config: LoggingConfig,
) -> AsyncGenerator[None]:
    """Async lifespan for future ASGI use: configure logging on startup, stop listener on shutdown.

    Args:
        a_config: Logging configuration.

    Yields:
        None — application is alive during yield.
    """
    listener: logging.handlers.QueueListener | None = None

    logging_result: Result[logging.handlers.QueueListener] = configure_logging(a_config)
    _logger.debug("Logging configured at level %s", a_config.level.upper())
    if logging_result.is_success():
        listener = logging_result.value

    _logger.info("Selma starting")

    try:
        yield
    finally:
        _logger.info("Selma stopped")
        if listener is not None:
            listener.stop()
