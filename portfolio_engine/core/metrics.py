"""Core numerical utilities used by selection and allocation modules."""

from typing import Any

import numpy as np
from numba import jit
from numpy import floating

# Floor for variance/std-like magnitudes: anything <= EPS is "no information"
# and maps to NaN semantics rather than infinities (C3 contract).
VOL_FLOOR_EPS = 1e-12


@jit(nopython=True, cache=True)
def compute_logarithmic_returns(price_series: np.ndarray) -> np.ndarray:
    """Compute log returns r_t = ln(P_t / P_{t-1}) for a 1D price series."""

    number_of_prices = len(price_series)
    log_returns = np.empty(number_of_prices - 1, dtype=np.float64)
    for i in range(1, number_of_prices):
        log_returns[i - 1] = np.log(price_series[i] / price_series[i - 1])
    return log_returns


@jit(nopython=True, cache=True)
def calculate_annualized_return(daily_log_returns: np.ndarray) -> floating[Any]:
    daily_mean_return = np.mean(daily_log_returns)
    return daily_mean_return * 252


@jit(nopython=True, cache=True)
def calculate_annualized_volatility(daily_log_returns: np.ndarray) -> float:
    """Annualized SAMPLE volatility: std(ddof=1) * sqrt(252).

    Manual computation because numba does not support np.std(..., ddof=);
    keeps the estimator consistent with the covariance kernel below.
    """
    n = len(daily_log_returns)
    if n < 2:
        return float("nan")
    mean_value = np.mean(daily_log_returns)
    sum_sq = 0.0
    for i in range(n):
        diff = daily_log_returns[i] - mean_value
        sum_sq += diff * diff
    sample_std = np.sqrt(sum_sq / (n - 1))
    return sample_std * np.sqrt(252.0)


def calculate_sharpe_ratio(annual_return: float, annual_volatility: float, risk_free_rate: float) -> float:
    """Risk-adjusted excess return; NaN (never inf) when vol is degenerate."""
    if not np.isfinite(annual_volatility) or annual_volatility <= VOL_FLOOR_EPS:
        return float("nan")
    return (annual_return - risk_free_rate) / annual_volatility


@jit(nopython=True, cache=True)
def calculate_correlation_matrix(returns_matrix: np.ndarray) -> np.ndarray:
    """Compute Pearson correlation matrix from a returns matrix [days, assets].

    Assets with zero variance produce NaN correlations against other assets.
    """

    number_of_days, number_of_assets = returns_matrix.shape

    if number_of_days <= 1:
        return np.full((number_of_assets, number_of_assets), np.nan, dtype=np.float64)

    centered_returns = np.empty_like(returns_matrix)
    for asset_index in range(number_of_assets):
        asset_mean = np.mean(returns_matrix[:, asset_index])
        for day_index in range(number_of_days):
            centered_returns[day_index, asset_index] = returns_matrix[day_index, asset_index] - asset_mean

    asset_standard_deviations = np.empty(number_of_assets, dtype=np.float64)
    for asset_index in range(number_of_assets):
        sum_of_squares = 0.0
        for day_index in range(number_of_days):
            sum_of_squares += centered_returns[day_index, asset_index] ** 2

        if sum_of_squares == 0.0:
            asset_standard_deviations[asset_index] = 0.0
        else:
            asset_standard_deviations[asset_index] = np.sqrt(sum_of_squares / (number_of_days - 1))

    correlation_matrix = np.empty((number_of_assets, number_of_assets), dtype=np.float64)

    for asset_i in range(number_of_assets):
        for asset_j in range(asset_i, number_of_assets):
            if asset_i == asset_j:
                # Honest diagonal: 1.0 only when there IS information (var>0).
                if asset_standard_deviations[asset_i] > VOL_FLOOR_EPS:
                    correlation_matrix[asset_i, asset_j] = 1.0
                else:
                    correlation_matrix[asset_i, asset_j] = np.nan
            else:
                if (
                    asset_standard_deviations[asset_i] <= VOL_FLOOR_EPS
                    or asset_standard_deviations[asset_j] <= VOL_FLOOR_EPS
                ):
                    correlation_coefficient = np.nan
                else:
                    cross_product = 0.0
                    for day_index in range(number_of_days):
                        cross_product += centered_returns[day_index, asset_i] * centered_returns[day_index, asset_j]

                    correlation_coefficient = cross_product / (
                        (number_of_days - 1)
                        * asset_standard_deviations[asset_i]
                        * asset_standard_deviations[asset_j]
                    )

                correlation_matrix[asset_i, asset_j] = correlation_coefficient
                correlation_matrix[asset_j, asset_i] = correlation_coefficient

    return correlation_matrix


@jit(nopython=True, cache=True)
def calculate_covariance_matrix(returns_matrix: np.ndarray) -> np.ndarray:
    number_of_days, number_of_assets = returns_matrix.shape

    if number_of_days <= 1:
        return np.full((number_of_assets, number_of_assets), np.nan, dtype=np.float64)

    centered_returns = np.empty_like(returns_matrix)
    for asset_index in range(number_of_assets):
        asset_mean = np.mean(returns_matrix[:, asset_index])
        for day_index in range(number_of_days):
            centered_returns[day_index, asset_index] = returns_matrix[day_index, asset_index] - asset_mean

    covariance_matrix = np.empty((number_of_assets, number_of_assets), dtype=np.float64)

    for asset_i in range(number_of_assets):
        for asset_j in range(asset_i, number_of_assets):
            cross_product = 0.0
            for day_index in range(number_of_days):
                cross_product += centered_returns[day_index, asset_i] * centered_returns[day_index, asset_j]

            covariance_value = cross_product / (number_of_days - 1)
            covariance_matrix[asset_i, asset_j] = covariance_value
            covariance_matrix[asset_j, asset_i] = covariance_value

    return covariance_matrix


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

    if set(prices_dictionary) != set(dates_dictionary):
        missing_dates = set(prices_dictionary) - set(dates_dictionary)
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
    return _correlation_distance_kernel(correlation_matrix, _METRIC_CODES[metric])


@jit(nopython=True, cache=True)
def _correlation_distance_kernel(correlation_matrix: np.ndarray, metric_code: int) -> np.ndarray:
    matrix_size = correlation_matrix.shape[0]
    distance_matrix = np.empty((matrix_size, matrix_size), dtype=np.float64)
    for i in range(matrix_size):
        for j in range(matrix_size):
            if i == j:
                distance_matrix[i, j] = 0.0
            else:
                corr_value = correlation_matrix[i, j]
                if metric_code == 1:
                    # signed: sqrt(0.5*(1-corr)); NaN propagates via arithmetic.
                    distance_matrix[i, j] = np.sqrt(0.5 * (1.0 - corr_value))
                else:
                    distance_matrix[i, j] = 1.0 - abs(corr_value)
    return distance_matrix

