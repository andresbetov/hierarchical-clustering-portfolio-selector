"""Minimal logging helpers for application scripts using portfolio_engine."""

import logging
from typing import Union


def configure_logging(level: Union[int, str] = logging.INFO) -> None:
    """Configure a simple console logger once.

    Safe to call multiple times; existing handlers are preserved.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

