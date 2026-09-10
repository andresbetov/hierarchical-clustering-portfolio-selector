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


def portfolio_return_series(prices_alineados: dict, weights: dict) -> np.ndarray:
    """In-sample daily log-return series of a fixed-weight portfolio (feat-046).

    Per-asset log diffs via compute_logarithmic_returns stacked in
    weights-dict key order, dotted with the weight vector in the same order
    (walk_forward.py:262-264 pattern, in-sample). A weight ticker WITHOUT
    aligned prices raises a named ValueError (uncomputable); aligned price
    series WITHOUT weight are zero-embedded (legacy M<N route,
    walk_forward.py:252-256 pattern) — key sets need not be equal, but every
    weight must be covered by prices. T prices yield T-1 returns.
    Callers MUST supply frames re-aligned with minimum_overlap_ratio=1.0
    over the final weight keys (feat-050 contract): 1.0 skips the 0.9 guard
    and reproduces the intersection-dropna the engine used, while 0.9 can
    exclude survivors on pathological calendars.
    """
    from ..core.metrics import compute_logarithmic_returns

    if not weights:
        raise ValueError(
            "empty weights — nothing to weight (feat-046; N=0 aborts upstream)"
        )
    missing = [t for t in weights if t not in prices_alineados]
    if missing:
        raise ValueError(
            f"Weight tickers without aligned prices: {missing} — "
            "every weighted ticker needs a price series (feat-046)"
        )
    ordered = list(weights)
    lengths = {t: len(np.asarray(prices_alineados[t])) for t in ordered}
    if len(set(lengths.values())) != 1:
        raise ValueError(
            f"ragged aligned price lengths: {lengths} — caller must re-align "
            "with minimum_overlap_ratio=1.0 over the final keys (feat-046)"
        )
    matrix = np.column_stack(
        [compute_logarithmic_returns(np.asarray(prices_alineados[t], dtype=np.float64)) for t in ordered]
    )
    weight_vector = np.array([weights[t] for t in ordered], dtype=np.float64)
    return matrix @ weight_vector


def tail_risk_metrics(
    daily_series,
    risk_free_rate: float,
    trading_days: int = 252,
) -> dict:
    """In-sample tail risk: log-coherent Sortino + historical VaR/CVaR95 (feat-046).

    Sortino = (mean(r)*T − ln(1+rf)) / downside_dev with the log-coherent
    daily target T_daily = ln(1+rf)/T via risk_free_log_rate (feat-036 —
    the tracker's rf/252 is recorded as errata, it mixes simple/log) and
    downside_dev = sqrt(mean(min(0, r − T_daily)^2)) * sqrt(T) over the TOTAL
    N (non-down days count as zero, Sortino-Forsey 1996). No down days ->
    Sortino/DD None with reason while VaR/CVaR stay numeric. VaR_95_daily =
    −quantile(r, 0.05, method="linear") pinned (NumPy 2.x; interpolation=
    was removed in 2.0); CVaR_95_daily = −mean(r | r<=q05), inclusive tail so
    it is never empty; cvar >= var (signed) ALWAYS, cvar >= |var| when VaR is
    non-negative (genuine loss tail). VaR/CVaR are NEVER sqrt-scaled (catalog
    §7 guard: tail is not Gaussian). len<2 or ANY non-finite observation ->
    all None + reason (never 0/inf; trimming points would fabricate a
    cleaner sample). Labels in-sample/daily/no-costs embedded.
    """
    from ..core.metrics import calculate_annualized_return, risk_free_log_rate

    if trading_days <= 0:
        raise ValueError(
            f"trading_days must be positive, got {trading_days} (feat-046)"
        )
    base: dict = {
        "sortino_ratio": None,
        "downside_deviation_annual": None,
        "var_95_daily": None,
        "cvar_95_daily": None,
        "target_daily": None,
        "risk_free_rate": risk_free_rate,
        "trading_days": trading_days,
        "n_obs": 0,
        "n_tail": 0,
        "frequency": "daily",
        "sample": "in-sample",
        "costs": "no-costs",
        "reason": None,
    }
    arr = np.asarray(daily_series, dtype=np.float64).ravel()
    if arr.size < 2:
        base["reason"] = "n_obs<2"
        return base
    if not np.all(np.isfinite(arr)):
        base["reason"] = "non-finite-observations"
        return base
    target_annual = risk_free_log_rate(risk_free_rate)
    if not np.isfinite(target_annual):
        base["reason"] = "non-finite-risk-free-target"
        return base
    target_daily = target_annual / trading_days
    base["target_daily"] = float(target_daily)
    base["n_obs"] = int(arr.size)

    shortfalls = np.minimum(0.0, arr - target_daily)
    downside_variance = float(np.mean(shortfalls**2))
    if downside_variance > 0.0:
        downside_dev = math.sqrt(downside_variance) * math.sqrt(trading_days)
        base["downside_deviation_annual"] = downside_dev
        excess = calculate_annualized_return(arr, trading_days) - target_annual
        base["sortino_ratio"] = excess / downside_dev
    else:
        base["reason"] = "no-downside-observations"

    q05 = float(np.quantile(arr, 0.05, method="linear"))
    # min(arr) <= q05 by monotonicity of correctly-rounded arithmetic, so the
    # inclusive tail is provably non-empty (no 1-ulp escape possible).
    tail = arr[arr <= q05]
    base["var_95_daily"] = -q05
    base["cvar_95_daily"] = float(-tail.mean())
    base["n_tail"] = int(tail.size)
    return base


def drawdown_metrics(daily_series, trading_days: int = 252) -> dict:
    """In-sample drawdown scalars from daily log returns (feat-046).

    P_t = exp(cumsum(r_t)) (exact twin of cumprod(1+r_simple) for log
    inputs — feeding log r into (1+r).cumprod would be wrong), DD_t =
    P_t/running_max(P_t) − 1 <= 0, max_drawdown = min(DD) (<= 0 invariant),
    calmar = mean(r)*T/|maxDD| (project convention: the same mean*T
    annualizer as Sharpe/Sortino — documented deviation from the geometric
    CAGR modern standard). |maxDD| <= VOL_FLOOR_EPS (flat series) ->
    calmar None with reason, never inf; negative Calmar (negative ann
    return) is legal and reported numeric. len<2 or ANY non-finite ->
    all None + reason. The drawdown CURVE is not serialized (scalars only,
    scope cut); labels in-sample/daily/no-costs embedded.
    """
    from ..core.metrics import VOL_FLOOR_EPS, calculate_annualized_return

    if trading_days <= 0:
        raise ValueError(
            f"trading_days must be positive, got {trading_days} (feat-046)"
        )
    base: dict = {
        "max_drawdown": None,
        "calmar_ratio": None,
        "annualized_return": None,
        "trading_days": trading_days,
        "n_obs": 0,
        "frequency": "daily",
        "sample": "in-sample",
        "costs": "no-costs",
        "reason": None,
    }
    arr = np.asarray(daily_series, dtype=np.float64).ravel()
    if arr.size < 2:
        base["reason"] = "n_obs<2"
        return base
    if not np.all(np.isfinite(arr)):
        base["reason"] = "non-finite-observations"
        return base
    base["n_obs"] = int(arr.size)
    with np.errstate(over="ignore"):  # overflow handled explicitly below
        wealth = np.exp(np.cumsum(arr))
    if not np.all(np.isfinite(wealth)):
        # Pathological compounding (cumsum ~1e3): exp overflows to inf and
        # inf/inf would leak nan + RuntimeWarning — report null, never nan.
        base["reason"] = "wealth-overflow-non-finite"
        return base
    drawdown = wealth / np.maximum.accumulate(wealth) - 1.0
    max_dd = float(drawdown.min())
    base["max_drawdown"] = max_dd
    ann_ret = calculate_annualized_return(arr, trading_days)
    base["annualized_return"] = ann_ret
    if abs(max_dd) <= VOL_FLOOR_EPS:
        base["reason"] = "flat-series"
        return base
    base["calmar_ratio"] = ann_ret / abs(max_dd)
    return base


def tree_diagnostics(covariance_matrix, linkage_method: str = "single") -> dict:
    """Hierarchical tree health: merge-depth, singleton accretion, flag (feat-048).

    Recomputes the linkage the engine would build (build_hrp_linkage) and
    reports: max_depth = longest root->leaf path COUNTING MERGES over Z
    (never the Y-axis height, which is causally irrelevant to count
    bisection); chaining_rate = merges with EXACTLY one leaf child / (n-1)
    (singleton accretion; an initial leaf-leaf pairing is grouping, not
    accretion — decided with the user after the >=1-leaf reading proved a
    0.5 floor with 0.818 on the healthy 12-block pattern); chaining_flag =
    depth > ceil(log2(n))+2 or rate > 0.60 (catalog §8 heuristic thresholds,
    echoed for auditability); leaf_order = the engine's own _leaf_order
    (machine-comparable with the dendrogram per runtime-diagnostics).
    n<2 -> metrics None + reason WITHOUT raising (pre-checked, so no broad
    try/except can swallow programmer errors); n==2 -> depth 1, rate 0.0
    (the single merge is leaf-leaf: XOR accretion is impossible), flag
    False (not pathological). Invalid method/covariance propagate the
    seam's ValueError (fail loud). Ward on precomputed signed
    distance is an approximation (SciPy linkage Note 2: ward assumes
    Euclidean) — documented, acceptance is finiteness. Cost O(n^2),
    deterministic, n<=12 trivial.
    """
    import math

    from ..portfolio.hrp import _leaf_order, build_hrp_linkage

    base: dict = {
        "linkage_method": linkage_method,
        "n_assets": 0,
        "max_depth": None,
        "depth_threshold": None,
        "chaining_rate": None,
        "rate_threshold": 0.60,
        "chaining_flag": None,
        "leaf_order": None,
        "reason": None,
    }
    try:
        cov = np.asarray(covariance_matrix, dtype=np.float64)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"covariance_matrix must be a 2-D numeric array, got ragged/object input: {exc} (feat-048)"
        ) from exc
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError(
            f"covariance_matrix must be square, got shape {cov.shape} (feat-048)"
        )
    n_assets = cov.shape[0]
    base["n_assets"] = n_assets
    if n_assets < 2:
        base["reason"] = "n_assets<2"
        return base
    linkage = build_hrp_linkage(cov, linkage_method=linkage_method)
    n_merges = n_assets - 1
    depth: dict = {}
    accretion = 0
    for i in range(n_merges):
        left, right = int(linkage[i, 0]), int(linkage[i, 1])
        # Z is produced by scipy linkage (never consumed externally), whose
        # ids increase row by row — children are always defined before row i,
        # so a single ordered pass suffices (no forward references possible).
        depth[n_assets + i] = 1 + max(depth.get(left, 0), depth.get(right, 0))
        if (left < n_assets) != (right < n_assets):
            accretion += 1
    max_depth = depth[2 * n_assets - 2]
    depth_threshold = math.ceil(math.log2(n_assets)) + 2
    chaining_rate = accretion / n_merges
    base["max_depth"] = max_depth
    base["depth_threshold"] = depth_threshold
    base["chaining_rate"] = chaining_rate
    base["leaf_order"] = [int(leaf) for leaf in _leaf_order(linkage, n_assets)]
    # n==2 carve-out (catalog: not pathological): depth 1 never exceeds its
    # threshold 3 and accretion is impossible, but the explicit gate documents
    # that a 2-asset tree is never flagged. Note an exact ==0.60 rate is
    # unreachable for any realistic n (leaf absorptions T+2L=n force
    # T/(n-1)!=3/5 by parity, and no other small-denominator fraction rounds
    # to the same double), so > vs >= is unobservable — no boundary pin.
    base["chaining_flag"] = bool(
        n_assets > 2 and (max_depth > depth_threshold or chaining_rate > base["rate_threshold"])
    )
    return base


def walk_forward_section(report) -> dict:
    """Walk-forward validation section: aggregates, per-fold detail, drift (feat-049).

    Consumes WalkForwardReport.to_dict() VERBATIM for the aggregates (the
    section medians are identical to the report's by construction; to_dict
    is never modified). Per-fold rows expose index, train/test positions
    (tuples become lists), tickers, weights, OOS return/volatility/sharpe,
    mandate_relaxed and benchmarks exactly as the engine built them —
    invalid folds (empty weights, None metrics, {} benchmarks) preserved,
    never synthesized. Drift (§9 catalog): consecutive VALID folds ordered
    by index (valid = oos_sharpe not None and finite), weights zero-embedded
    over the pair's ticker union (entries/exits charged at face value),
    l1 = sum|w_k − w_{k-1}| in [0,2] for fully-invested long-only books;
    median_l1 (np.median), p90_l1 (quantile method="linear", H&F-7, VaR
    precedent), pairs_computed/pairs_possible, broken_pairs, label
    drift-not-turnover. An invalid fold BREAKS the chain (no interpolation,
    GIPS-style: never link across a break). <2 valid folds -> drift None +
    reason. Drift is stability telemetry, NEVER annualized nor multiplied
    by bps (L1 = 2x one-way turnover-equiv; costs need prices/spreads per
    Perold 1988, explicitly out of scope). Weight books are trusted engine
    output (no sum-1 re-validation: L1 in [0,2] holds long-only).
    """
    folds = list(report.folds)
    drift = _drift_section(folds)
    return {
        "aggregates": dict(report.to_dict()),
        "folds": [_fold_row(fold) for fold in folds],
        "drift": drift,
    }


def _fold_row(fold) -> dict:
    """One audit row, verbatim engine values (positions serialized)."""
    return {
        "index": fold.index,
        "train_positions": [fold.train_positions[0], fold.train_positions[1]],
        "test_positions": [fold.test_positions[0], fold.test_positions[1]],
        "tickers": list(fold.tickers),
        "weights": dict(fold.weights),
        "oos_return": fold.oos_return,
        "oos_volatility": fold.oos_volatility,
        "oos_sharpe": fold.oos_sharpe,
        "mandate_relaxed": fold.mandate_relaxed,
        # Deep-copy one level down: inner "weights" dicts must not alias the
        # live WalkForwardFold (a consumer mutating the section must never
        # mutate the engine report).
        "benchmarks": {
            name: {**entry, "weights": dict(entry.get("weights", {}))}
            for name, entry in fold.benchmarks.items()
        },
    }


def _drift_section(folds: list) -> dict:
    """L1 drift over consecutive valid folds (see walk_forward_section)."""
    base: dict = {
        "median_l1": None,
        "p90_l1": None,
        "pairs_computed": 0,
        "pairs_possible": max(0, len(folds) - 1),
        "broken_pairs": [],
        "label": "drift-not-turnover",
        "reason": None,
    }

    def _valid(fold) -> bool:
        return fold.oos_sharpe is not None and np.isfinite(fold.oos_sharpe)

    computed = []
    for prev, curr in zip(folds, folds[1:]):
        if _valid(prev) and _valid(curr):
            universe = sorted(set(prev.tickers) | set(curr.tickers))
            l1 = float(
                sum(abs(prev.weights.get(t, 0.0) - curr.weights.get(t, 0.0)) for t in universe)
            )
            computed.append(l1)
        else:
            base["broken_pairs"].append([prev.index, curr.index])
    base["pairs_computed"] = len(computed)
    if len(computed) < 1:
        if sum(1 for fold in folds if _valid(fold)) < 2:
            base["reason"] = "need-2-valid-folds"
        else:
            # Every adjacent pair broken (e.g. alternating valid/invalid):
            # nothing computable, and the breakage itself is the signal.
            base["reason"] = "all-pairs-broken"
        return base
    values = np.array(computed, dtype=np.float64)
    base["median_l1"] = float(np.median(values))
    base["p90_l1"] = float(np.quantile(values, 0.9, method="linear"))
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
    "drawdown_metrics",
    "dump_technical_report",
    "portfolio_return_series",
    "sanitize_json_payload",
    "tail_risk_metrics",
    "tree_diagnostics",
    "walk_forward_section",
]
