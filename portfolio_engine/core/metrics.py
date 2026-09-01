"""Core numerical utilities used by selection and allocation modules.

Fully vectorized NumPy (feat-022 removed numba): at the project's scale
(decenas-centenas de activos x ~1250 dias) JIT warm-up dominates runtime
gains, while the characterization suite pins exact semantics.
"""

import math

import numpy as np
from sklearn.covariance import OAS, LedoitWolf

# Floor for variance/std-like magnitudes: anything <= EPS is "no information"
# and maps to NaN semantics rather than infinities (C3 contract).
VOL_FLOOR_EPS = 1e-12


def risk_free_log_rate(risk_free_rate: float) -> float:
    """Continuously-compounded risk-free rate ln(1+rf), stable for rf << 1.

    Returns NaN for non-finite rf or domain error (rf <= -1) to preserve
    the "never inf" contract of calculate_sharpe_ratio.
    """
    if not np.isfinite(risk_free_rate):
        return float("nan")
    if risk_free_rate <= -1:
        return float("nan")
    return math.log1p(risk_free_rate)


def compute_logarithmic_returns(price_series: np.ndarray) -> np.ndarray:
    """Compute log returns r_t = ln(P_t / P_{t-1}) for a 1D price series."""
    prices = np.asarray(price_series, dtype=np.float64)
    if len(prices) < 2:
        return np.empty(0, dtype=np.float64)
    return np.log(prices[1:] / prices[:-1])


def calculate_annualized_return(daily_log_returns: np.ndarray, trading_days: int = 252) -> float:
    daily_mean_return = np.mean(daily_log_returns)
    return float(daily_mean_return * trading_days)


def calculate_annualized_volatility(daily_log_returns: np.ndarray, trading_days: int = 252) -> float:
    """Annualized SAMPLE volatility: std(ddof=1) * sqrt(trading_days)."""
    n = len(daily_log_returns)
    if n < 2:
        return float("nan")
    return float(np.std(daily_log_returns, ddof=1) * np.sqrt(trading_days))


def calculate_sharpe_ratio(annual_return: float, annual_volatility: float, risk_free_rate: float) -> float:
    """Risk-adjusted excess return; NaN (never inf) when vol is degenerate.

    Coherencia logarítmica: annual_return es log anualizado (mean(log)*252),
    por lo que el exceso usa rf_log = ln(1+rf) (math.log1p, estable).
    """
    if not np.isfinite(annual_volatility) or annual_volatility <= VOL_FLOOR_EPS:
        return float("nan")
    rf_log = risk_free_log_rate(risk_free_rate)
    if not np.isfinite(rf_log) or not np.isfinite(annual_return):
        return float("nan")
    return (annual_return - rf_log) / annual_volatility


def _validate_observations_matrix(returns_matrix: np.ndarray) -> tuple[np.ndarray, int, int]:
    matrix = np.asarray(returns_matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] <= 1:
        number_of_assets = matrix.shape[1] if matrix.ndim == 2 else 0
        return np.full((number_of_assets, number_of_assets), np.nan), 0, number_of_assets
    return matrix, matrix.shape[0], matrix.shape[1]


def calculate_correlation_matrix(returns_matrix: np.ndarray) -> np.ndarray:
    """Pearson correlation matrix from a returns matrix [days, assets].

    Honest diagonal (C3): 1.0 only when the asset has positive sample std;
    rows/columns of flat assets are NaN everywhere.
    """
    matrix, number_of_days, number_of_assets = _validate_observations_matrix(returns_matrix)
    if number_of_days == 0:
        return matrix

    centered = matrix - matrix.mean(axis=0, keepdims=True)
    sum_of_squares = (centered**2).sum(axis=0)
    standard_deviations = np.sqrt(sum_of_squares / (number_of_days - 1))

    cross_products = centered.T @ centered / (number_of_days - 1)

    outer_std = np.outer(standard_deviations, standard_deviations)
    with np.errstate(divide="ignore", invalid="ignore"):
        correlation = cross_products / outer_std

    # Flat assets: full NaN row/column including their own diagonal.
    degenerate = standard_deviations <= VOL_FLOOR_EPS
    correlation[degenerate, :] = np.nan
    correlation[:, degenerate] = np.nan

    informative = ~degenerate
    correlation[np.diag(informative)] = 1.0

    if not degenerate.any():
        np.fill_diagonal(correlation, 1.0)

    return correlation


def calculate_covariance_matrix(returns_matrix: np.ndarray) -> np.ndarray:
    """Sample covariance (ddof=1) from a returns matrix [days, assets]."""
    matrix, number_of_days, number_of_assets = _validate_observations_matrix(returns_matrix)
    if number_of_days == 0:
        return matrix

    centered = matrix - matrix.mean(axis=0, keepdims=True)
    return centered.T @ centered / (number_of_days - 1)


COVARIANCE_ESTIMATORS = ("sample", "ledoit_wolf", "oas")


def estimate_covariance(returns_matrix: np.ndarray, method: str = "sample") -> np.ndarray:
    """Single covariance-estimation seam (ADR 005).

    - "sample": the legacy ddof=1 sample covariance (bit-identical to
      calculate_covariance_matrix — the default, no silent behavior change).
    - "ledoit_wolf" / "oas": scikit-learn shrinkage estimators
      (parity-tested against sklearn.covariance at 1e-12).

    Degenerate inputs (<= 1 observation) return the full-NaN matrix without
    invoking sklearn, mirroring calculate_covariance_matrix semantics.
    """
    if method not in COVARIANCE_ESTIMATORS:
        raise ValueError(
            f"Unknown covariance_estimator '{method}'; allowed: {list(COVARIANCE_ESTIMATORS)}"
        )

    matrix, number_of_days, _ = _validate_observations_matrix(returns_matrix)
    if number_of_days == 0:
        return matrix
    if method == "sample":
        return calculate_covariance_matrix(returns_matrix)

    estimator = LedoitWolf() if method == "ledoit_wolf" else OAS()
    return estimator.fit(matrix).covariance_


def construct_returns_matrix(prices_dictionary: dict) -> np.ndarray:
    """Build matrix [days, assets] preserving insertion order from input dict.

    This ordering must stay consistent with the metrics dict used downstream.
    Raises ValueError if lengths differ: position-wise stacking of misaligned
    series silently compares different trading days (use
    align_prices_to_common_calendar first).
    """

    asset_names = list(prices_dictionary.keys())
    lengths = {name: len(np.asarray(v)) for name, v in prices_dictionary.items()}
    if len(set(lengths.values())) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in lengths.items())
        raise ValueError(
            "Misaligned price series passed to construct_returns_matrix "
            f"(lengths differ: {detail}); align calendars first."
        )
    returns_list = []

    for asset_name in asset_names:
        price_array = np.asarray(prices_dictionary[asset_name], dtype=np.float64)
        daily_returns = compute_logarithmic_returns(price_array)
        # Preserve dict insertion order so downstream correlation, covariance, and
        # allocation steps all refer to the same asset positions.
        returns_list.append(daily_returns)

    return np.array(returns_list).T


MIN_COMMON_ROWS = 2


def align_prices_to_common_calendar(prices_dictionary: dict, dates_dictionary: dict) -> dict:
    """Trim every price series to the common calendar (inner join on dates).

    Returns a dict with the same ticker order as `prices_dictionary`, where
    each value is the array trimmed to rows present for ALL tickers and sorted
    ascending. Raises ValueError when fewer than MIN_COMMON_ROWS common dates
    exist or when any series/index pair has mismatched lengths.
    """
    import pandas as pd

    # One-directional requirement: every PRICE series must have dates; extra
    # date entries are legitimate (e.g. tickers filtered out downstream still
    # feed charts from the same dict).
    missing_dates = [ticker for ticker in prices_dictionary if ticker not in dates_dictionary]
    if missing_dates:
        raise ValueError(f"Missing dates entry for tickers: {sorted(missing_dates)}")

    columns = {}
    for ticker, prices in prices_dictionary.items():
        dates_index = pd.DatetimeIndex(dates_dictionary[ticker])
        values = np.asarray(prices)
        if len(values) != len(dates_index):
            raise ValueError(
                f"Ticker {ticker}: {len(values)} prices vs {len(dates_index)} dates"
            )
        columns[ticker] = pd.Series(values.astype(np.float64), index=dates_index)

    frame = pd.DataFrame(columns).sort_index()
    frame = frame.dropna(how="any")

    if len(frame) < MIN_COMMON_ROWS:
        tickers = list(prices_dictionary)
        first, second = tickers[0], tickers[-1]
        raise ValueError(
            f"Calendar intersection too small ({len(frame)} rows < {MIN_COMMON_ROWS}) "
            f"across tickers={tickers}; e.g. span {first}..{second}."
        )

    return {
        ticker: frame[ticker].to_numpy(dtype=np.float64)
        for ticker in prices_dictionary
    }


_METRIC_CODES = {"signed": 1, "abs": 0}


def compute_correlation_distance_matrix(correlation_matrix: np.ndarray, metric: str = "signed") -> np.ndarray:
    """Clustering distance from correlations, per ADR 002.

    - "signed": d = sqrt(0.5*(1-corr)) — negative correlation means maximum
      distance (diversifiers are never merged with their hedge partners).
    - "abs": legacy d = 1-|corr| — collapses sign, kept for reproducibility
      of historical behavior on demand.
    NaN entries (flat assets) propagate honestly in both modes.
    """
    if metric not in _METRIC_CODES:
        raise ValueError(f"Unknown distance metric '{metric}'; allowed: {sorted(_METRIC_CODES)}")

    corr = np.asarray(correlation_matrix, dtype=np.float64)
    size = corr.shape[0]
    distance = np.empty((size, size), dtype=np.float64)

    if _METRIC_CODES[metric] == 1:  # signed
        upper = np.sqrt(0.5 * (1.0 - corr))
    else:  # abs
        upper = 1.0 - np.abs(corr)

    i_upper = np.triu_indices(size, k=1)
    distance[i_upper] = upper[i_upper]
    distance.T[i_upper] = upper[i_upper]
    np.fill_diagonal(distance, 0.0)
    return distance
