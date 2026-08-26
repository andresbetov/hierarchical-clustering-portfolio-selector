"""Package-scoped logging helpers for applications using portfolio_engine."""

import logging
import os
import sys

_PACKAGE_LOGGER_NAME = "portfolio_engine"
_HANDLER_TAG = "_portfolio_engine_stream_handler"


def _resolve_level(explicit: int | str | None) -> int:
    """Resolve effective level: explicit param > LOG_LEVEL env > INFO.

    Note on stdlib semantics: `logging.getLevelName()` maps name->level ONLY
    when given a string; given an int it returns the level *name* (string).
    Hence ints are returned directly and strings go through the lookup.

    An invalid env value warns and falls back to INFO instead of failing
    the process (robustness for shell-embedded invocations).
    """
    if isinstance(explicit, bool):
        explicit = None

    if isinstance(explicit, int):
        return explicit

    if isinstance(explicit, str):
        resolved = logging.getLevelName(explicit.strip().upper())
        if isinstance(resolved, int):
            return resolved
        # Invalid explicit string: warn once and continue down the chain.

    env_value = os.environ.get("LOG_LEVEL")
    if not env_value:
        return logging.INFO

    resolved = logging.getLevelName(env_value.strip().upper())
    if isinstance(resolved, int):
        return resolved

    package_logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    package_logger.warning(
        "Invalid LOG_LEVEL value ignored: value=%s valid=%s falling_back=INFO",
        env_value,
        "CRITICAL|ERROR|WARNING|INFO|DEBUG|NOTSET",
    )
    return logging.INFO


def configure_logging(level: int | str | None = None) -> None:
    """Configure the package logger exactly once; later calls only adjust level.

    - Attaches a dedicated StreamHandler(stderr) under the "portfolio_engine"
      logger so module loggers (portfolio_engine.*) inherit it.
    - Does NOT touch the root logger: pytest caplog and third-party logs stay
      isolated from this application's handler.
    - Level precedence: explicit `level` argument > LOG_LEVEL env var > INFO.
    """
    package_logger = logging.getLogger(_PACKAGE_LOGGER_NAME)

    existing = getattr(package_logger, _HANDLER_TAG, None)
    if existing is None:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
        handler.name = _HANDLER_TAG
        setattr(package_logger, _HANDLER_TAG, handler)
        package_logger.addHandler(handler)
        package_logger.propagate = False
        # First configuration takes the requested/env level outright.
        package_logger.setLevel(_resolve_level(level))
        return

    # Re-invocation: keep single handler, refresh level only when explicit.
    if level is not None:
        package_logger.setLevel(_resolve_level(level))
