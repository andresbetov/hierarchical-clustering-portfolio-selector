"""Machine-readable technical report core (feat-043).

Pure serialization primitives for the JSON report epic: strict-JSON
sanitizer, single-file writer, deterministic config fingerprint and the
versioned envelope. No pipeline/CLI integration lives here (feat-050/051).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
from datetime import date, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = 1
_FINGERPRINT_HEX_CHARS = 16
_ENGINE_PACKAGE = "hierarchical-clustering-portfolio-selector"


def _to_iso8601(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return value.isoformat()


def sanitize_json_payload(obj: Any) -> Any:
    """Recursively convert a payload into strict-JSON-native primitives.

    ndarray -> list, numpy scalars -> Python scalars (.item() first because
    np.float64 subclasses float), non-finite floats -> None (JSON has no
    NaN/Infinity), tuples -> lists, Path -> str, date/datetime -> ISO-8601.
    """
    if isinstance(obj, np.ndarray):
        return sanitize_json_payload(obj.tolist())
    if isinstance(obj, np.generic):
        return sanitize_json_payload(obj.item())
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return _to_iso8601(obj)
    if isinstance(obj, tuple):
        return [sanitize_json_payload(item) for item in obj]
    if isinstance(obj, dict):
        return {str(key): sanitize_json_payload(value) for key, value in obj.items()}
    if isinstance(obj, (list,)):
        return [sanitize_json_payload(item) for item in obj]
    return obj


def dump_technical_report(payload: dict, path: Path | str) -> None:
    """Write exactly one JSON file per run, overwriting any previous report.

    Creates the parent directory. Raises ValueError on any non-finite float
    that escaped sanitization (allow_nan=False), never emitting invalid JSON.
    """
    sanitized = sanitize_json_payload(payload)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(sanitized, handle, allow_nan=False, indent=2, sort_keys=True)


def config_fingerprint(
    config,
    tickers: list[str],
    window_start: str,
    window_end: str,
) -> str:
    """Deterministic 16-hex fingerprint of config + universe + data window.

    Canonical serialization (sorted keys, json.dumps) of the frozen
    dataclass plus the sorted upper-cased universe and the resolved span.
    Deterministic across runs: no uuid, no wall-clock in the preimage.
    """
    universe = json.dumps(sorted(t.upper() for t in tickers))
    window = json.dumps({"start": window_start, "end": window_end})
    engine = _engine_version()
    preimage = json.dumps(
        {"config": config, "universe": universe, "window": window, "engine": engine},
        sort_keys=True,
        default=_canonical_default,
    )
    digest = hashlib.sha256(preimage.encode("utf-8")).hexdigest()
    return digest[:_FINGERPRINT_HEX_CHARS]


def _canonical_default(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def _engine_version() -> str:
    try:
        return version(_ENGINE_PACKAGE)
    except PackageNotFoundError:
        return "unknown"


def compute_filter_rejections(
    requested_tickers: list[str],
    asset_metrics: dict,
    filtered_metrics: dict,
    closing_prices: dict,
    config,
) -> dict:
    """Per-ticker filter funnel with signed threshold distances (feat-044).

    Pure re-derivation of the production screen order (selection.py:47-63):
    non-finite sharpe -> non-finite vol -> below min sharpe -> above max vol;
    survivors then split kept vs overlap_pruned by membership in the final
    filtered set (the POST-calendar-prune set main() returns, pipeline.py:122).
    No re-execution of apply_asset_filters: same guard order guarantees reason
    parity without duplicating its warning. Distances: d_sharpe = sharpe -
    minimum_sharpe_threshold, d_vol = maximum_volatility_threshold - vol
    (negative = excluded by that gate); BOTH None when any metric is
    non-finite. A requested ticker missing from either asset_metrics or
    closing_prices never ingested -> ingestion_rejected. Duplicate tickers
    are deduplicated (first occurrence wins) so tickers and counts agree.
    """

    def _finite_number(value) -> bool:
        return isinstance(value, (int, float)) and math.isfinite(value)

    # Duplicates classify once; requested counts reflect the unique universe
    # so tickers and counts never diverge.
    unique_requested = list(dict.fromkeys(requested_tickers))
    tickers_report = {}
    kept = 0
    for ticker in unique_requested:
        metrics = asset_metrics.get(ticker)
        if metrics is None or ticker not in closing_prices:
            tickers_report[ticker] = {"reason": "ingestion_rejected", "d_sharpe": None, "d_vol": None}
            continue

        sharpe = metrics.get("sharpe_ratio")
        vol = metrics.get("annual_volatility")
        if not _finite_number(sharpe):
            tickers_report[ticker] = {"reason": "sharpe_non_finite", "d_sharpe": None, "d_vol": None}
            continue
        if not _finite_number(vol):
            tickers_report[ticker] = {"reason": "vol_non_finite", "d_sharpe": None, "d_vol": None}
            continue

        d_sharpe = sharpe - config.minimum_sharpe_threshold
        d_vol = config.maximum_volatility_threshold - vol
        if sharpe < config.minimum_sharpe_threshold:
            tickers_report[ticker] = {"reason": "below_min_sharpe", "d_sharpe": d_sharpe, "d_vol": d_vol}
        elif vol > config.maximum_volatility_threshold:
            tickers_report[ticker] = {"reason": "above_max_vol", "d_sharpe": d_sharpe, "d_vol": d_vol}
        elif ticker in filtered_metrics:
            tickers_report[ticker] = {"reason": "kept", "d_sharpe": d_sharpe, "d_vol": d_vol}
            kept += 1
        else:
            tickers_report[ticker] = {"reason": "overlap_pruned", "d_sharpe": d_sharpe, "d_vol": d_vol}

    return {
        "thresholds": {
            "min_sharpe": config.minimum_sharpe_threshold,
            "max_volatility": config.maximum_volatility_threshold,
        },
        "tickers": tickers_report,
        "counts": {
            "requested": len(unique_requested),
            "kept": kept,
            "rejected": len(unique_requested) - kept,
        },
    }


def build_report_envelope(
    tickers: list[str],
    config,
    window_start: str,
    window_end: str,
    generated_at: str,
) -> dict:
    """Versioned envelope: schema_version=1 + fingerprint + run_id.

    Sections of the report (diagnostics) are optional under schema_version=1;
    a consumer of an intermediate artifact sees fewer keys without breaking.
    run_id is DERIVED from the fingerprint — uuid randomness is forbidden
    (system-verification determinism contract, feat-030).
    """
    fingerprint = config_fingerprint(config, tickers, window_start, window_end)
    return {
        "schema_version": SCHEMA_VERSION,
        "fingerprint": fingerprint,
        "run_id": fingerprint,
        "generated_at": generated_at,
        "engine_version": _engine_version(),
        "universe": sorted(t.upper() for t in tickers),
        "window": {"start": window_start, "end": window_end},
    }


__all__ = [
    "SCHEMA_VERSION",
    "build_report_envelope",
    "compute_filter_rejections",
    "config_fingerprint",
    "dump_technical_report",
    "sanitize_json_payload",
]
