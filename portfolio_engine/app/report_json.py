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


def allocation_diagnostics(
    weights: dict,
    covariance_matrix: np.ndarray,
    covariance_tickers: list,
    config,
    raw_weights: np.ndarray | None = None,
) -> dict:
    """Allocation diagnostics: concentration, diversification, Dykstra drift (feat-045).

    HHI/N_eff with the sum-mandate verified (engine tolerance 1e-9) and the
    long-only mandate enforced. N_eff is Herfindahl-based 1/HHI (weight
    concentration), NOT Meucci entropy-based effective number of bets. DR =
    sum(w*sigma)/sigma_p and RC_i = w_i*(Sigma w)_i/sigma_p^2 ALWAYS computed
    on the covariance sliced to the weight subset via
    create_portfolio_covariance_matrix (feat-028 rule — N x N with an M-vector
    is dimensionally invalid); raw_vs_constrained Dykstra telemetry: caller
    raw_weights used verbatim for ANY method, deterministic HRP recompute
    (bit-identical seam, calculate_hrp_weights) only when method is hrp and
    the covariance matches the weight subset — HRP with a legacy M<N full
    covariance yields raw_vs_constrained None (a recompute on the slice would
    not be the engine's raw vector, and fabricating telemetry is dishonest);
    None for non-HRP without raw_weights (legacy raw vectors are not
    exposed). Bit-identity with the engine's raw vector requires the weights
    dict to iterate in covariance_tickers order (the pipeline contract);
    permuted callers get internally aligned telemetry but not the engine's
    bit-identical raw vector. Note: the effective-bounds resolution logs
    CRITICAL for relaxed universes on every call (documented duplication).
    Changed-count gate (diff > 1e-12) is a float-noise filter, not a mandate
    tolerance. Contract split: unknown ticker / shape mismatch / sum != 1
    / short weights raise (programmer error fails loud — spec'd for
    sum/mandate, feat-028 for alignment);
    degenerate-but-valid inputs (N=0, sigma_p at/below the floor, non-finite
    weights, degenerate HRP recompute) yield null/NaN via the strict-JSON
    sanitizer, never inf.
    """
    from ..core.config import _WEIGHT_SUM_TOLERANCE
    from ..core.metrics import VOL_FLOOR_EPS
    from ..portfolio.allocation import (
        _resolve_effective_bounds,
        calculate_portfolio_variance,
        create_portfolio_covariance_matrix,
    )
    from ..portfolio.hrp import calculate_hrp_weights

    n_assets = len(weights)
    base = {
        "method": config.weight_allocation_method,
        "n_assets": n_assets,
        "hhi": None,
        "n_effective": None,
        "diversification_ratio": None,
        "risk_contributions": None,
        "rc_spread": None,
        "raw_vs_constrained": None,
    }
    if n_assets == 0:
        return base

    missing = [t for t in weights if t not in covariance_tickers]
    # Precedence: N=0 returned above (no guards fire on the empty universe);
    # duplicates raise before unknown-ticker so row misalignment is reported
    # as misalignment, not as a missing ticker.
    if len(set(covariance_tickers)) != len(covariance_tickers):
        raise ValueError(
            "Duplicate tickers in covariance_tickers — rows must map 1:1 to "
            "tickers, first-occurrence binding would mask misalignment (feat-028)"
        )
    if missing:
        raise ValueError(
            f"Weight tickers not in covariance_tickers: {missing} — "
            "covariance rows must cover every weighted ticker (feat-028)"
        )
    if len(covariance_tickers) != covariance_matrix.shape[0]:
        raise ValueError(
            f"covariance_tickers has {len(covariance_tickers)} entries but the "
            f"covariance matrix has {covariance_matrix.shape[0]} rows — they must match"
        )

    weight_vector = np.array([weights[t] for t in weights], dtype=np.float64)
    if not np.all(np.isfinite(weight_vector)):
        base["hhi"] = float("nan")
        base["n_effective"] = float("nan")
        return base
    if abs(float(weight_vector.sum()) - 1.0) > _WEIGHT_SUM_TOLERANCE:
        raise ValueError(
            f"Weights must sum to 1 within {_WEIGHT_SUM_TOLERANCE}, got {weight_vector.sum()!r}"
        )
    negative = [t for t, w in weights.items() if w < 0]
    if negative:
        raise ValueError(
            f"Long-only mandate violated: negative weights at {negative} — "
            "HHI/N_eff/DR interpretation assumes long-only weights"
        )

    base["hhi"] = float(np.sum(weight_vector**2))
    base["n_effective"] = 1.0 / base["hhi"]

    sub_cov = create_portfolio_covariance_matrix(
        weights, covariance_matrix, {t: None for t in covariance_tickers}
    )
    portfolio_variance = calculate_portfolio_variance(weight_vector, sub_cov)
    # Guard the variance BEFORE sqrt: equivalent to sigma_p > VOL_FLOOR_EPS
    # (sqrt is monotonic on finite non-negatives) but never takes sqrt of a
    # negative on indefinite slices — no RuntimeWarning, risk stays None.
    if np.isfinite(portfolio_variance) and portfolio_variance > VOL_FLOOR_EPS**2:
        sigma_p = float(np.sqrt(portfolio_variance))
        weighted_avg_vol = float(weight_vector @ np.sqrt(np.diag(sub_cov)))
        diversification_ratio = weighted_avg_vol / sigma_p
        risk_vector = weight_vector * (sub_cov @ weight_vector) / portfolio_variance
        risk_contributions = {t: float(rc) for t, rc in zip(weights, risk_vector)}
        base["diversification_ratio"] = diversification_ratio
        base["risk_contributions"] = risk_contributions
        base["rc_spread"] = {
            "std": float(np.std(np.array(list(risk_contributions.values())))),
            "max_minus_min": float(max(risk_contributions.values()) - min(risk_contributions.values())),
            "max_over_equal": float(max(risk_contributions.values()) * n_assets),
        }

    if config.weight_allocation_method == "hrp" or raw_weights is not None:
        if raw_weights is None and n_assets == covariance_matrix.shape[0]:
            try:
                raw_weights = calculate_hrp_weights(sub_cov, linkage_method=config.linkage_method)
            except ValueError:
                # Degenerate covariance: the engine itself rejects it
                # (hrp.py guards), so there is no raw vector to report.
                # NOTE: config.linkage_method is validated at PortfolioConfig
                # construction, so a ValueError here is degeneracy, not config.
                raw_weights = None
        raw = None
        if raw_weights is not None:
            raw = np.asarray(raw_weights, dtype=np.float64)
            if not np.all(np.isfinite(raw)):
                raw = None  # unusable raw: no contradictory telemetry
            elif raw.shape != weight_vector.shape:
                raise ValueError(
                    f"raw_weights shape {raw.shape} does not match the weight subset "
                    f"({n_assets}) — raw_weights must be aligned to weights dict key order"
                )
        if raw is not None:
            diff = np.abs(raw - weight_vector)
            min_eff, max_eff = _resolve_effective_bounds(n_assets, config)
            base["raw_vs_constrained"] = {
                "l1_raw_to_constrained": float(diff.sum()),
                "max_weight_drop": float(max(raw - weight_vector)),
                "n_weights_changed": int(np.count_nonzero(diff > 1e-12)),
                "effective_bounds": {"min": min_eff, "max": max_eff},
                "mandate_relaxed": (
                    min_eff != config.minimum_single_asset_weight
                    or max_eff != config.maximum_single_asset_weight
                ),
            }
    return base


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
    "allocation_diagnostics",
    "compute_filter_rejections",
    "config_fingerprint",
    "dump_technical_report",
    "sanitize_json_payload",
]
