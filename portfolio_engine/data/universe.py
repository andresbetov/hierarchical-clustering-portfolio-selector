"""External universe loading (B2): tickers live in config, not in code."""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_UNIVERSE_PATH = Path("config/universe.yaml")


def load_universe(path: str | Path | None = None) -> list[str]:
    """Load the ticker universe from a YAML file.

    Expected schema (minimal):
        universe:
          - AAAA
          - BBBB

    Raises ValueError with a named reason on: missing file, missing `universe`
    key, non-list contents, empty list, or non-string entries.
    """
    resolved = Path(path) if path else DEFAULT_UNIVERSE_PATH

    if not resolved.exists():
        raise ValueError(
            f"Universe file not found: {resolved} — create it under config/ "
            "or pass --universe explicitly"
        )

    with resolved.open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)

    if not isinstance(document, dict) or "universe" not in document:
        raise ValueError(f"Universe file must define a top-level 'universe' key: {resolved}")

    entries = document["universe"]
    if not isinstance(entries, list) or len(entries) == 0:
        raise ValueError(f"'universe' must be a non-empty list: {resolved}")

    if not all(isinstance(entry, str) and entry.strip() for entry in entries):
        raise ValueError(f"'universe' entries must be non-empty strings: {resolved}")

    cleaned = [entry.strip().upper() for entry in entries]
    logger.info("Universe loaded: count=%d source=%s", len(cleaned), resolved)
    return cleaned
