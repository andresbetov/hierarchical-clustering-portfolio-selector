"""Portfolio weight construction from selected assets and covariance inputs."""
import logging

import numpy as np
from numba import jit

from ..core.config import PortfolioConfig
from ..core.metrics import VOL_FLOOR_EPS

logger = logging.getLogger(__name__)


def create_portfolio_covariance_matrix(
    optimal_portfolio: dict,
    full_covariance_matrix: np.ndarray,
    all_filtered_metrics: dict,
) -> np.ndarray:
    """Slice the full covariance matrix to the selected portfolio order."""

    all_tickers = list(all_filtered_metrics.keys())
    portfolio_tickers = list(optimal_portfolio.keys())

    # Keep the covariance matrix aligned to the filtered ticker order because the
    # weighting methods assume the same asset sequence end-to-end.
    portfolio_indices = [all_tickers.index(ticker) for ticker in portfolio_tickers]

    portfolio_cov_matrix = np.zeros((len(portfolio_tickers), len(portfolio_tickers)))
    for i, idx_i in enumerate(portfolio_indices):
        for j, idx_j in enumerate(portfolio_indices):
            portfolio_cov_matrix[i, j] = full_covariance_matrix[idx_i, idx_j]
    return portfolio_cov_matrix


@jit(nopython=True, cache=True)
def calculate_portfolio_variance(weights: np.ndarray, covariance_matrix: np.ndarray) -> float:
    return np.dot(weights, np.dot(covariance_matrix, weights))


@jit(nopython=True, cache=True)
def calculate_portfolio_return(weights: np.ndarray, expected_returns: np.ndarray) -> float:
    return np.dot(weights, expected_returns)


def calculate_equal_weights(number_of_assets: int) -> np.ndarray:
    return np.asarray(np.ones(number_of_assets) / number_of_assets, dtype=np.float64)


def calculate_inverse_volatility_weights(asset_volatilities: np.ndarray) -> np.ndarray:
    """Inverse-volatility weights; degenerate vols floored at VOL_FLOOR_EPS (M10)."""
    floored = np.maximum(np.asarray(asset_volatilities, dtype=np.float64), VOL_FLOOR_EPS)
    inverse_volatilities = np.asarray(1.0 / floored, dtype=np.float64)
    return inverse_volatilities / np.sum(inverse_volatilities)


def calculate_risk_parity_weights(
    covariance_matrix: np.ndarray,
    max_iterations: int = 1000,
    tolerance: float = 1e-8,
) -> np.ndarray:
    """Iteratively rebalance to equalize risk contribution per asset.

    Numerically guarded (C3): risk contributions are floored at
    VOL_FLOOR_EPS and per-iteration scaling factors are capped to [0.1, 10]
    so singular/near-singular covariance matrices cannot explode the update.
    Emits a warning when the iteration budget is exhausted without reaching
    `tolerance` (previously silent).
    """

    n_assets = covariance_matrix.shape[0]
    weights = np.ones(n_assets) / n_assets

    converged = False
    for _ in range(max_iterations):
        portfolio_variance = float(calculate_portfolio_variance(weights, covariance_matrix))
        if not np.isfinite(portfolio_variance) or portfolio_variance <= VOL_FLOOR_EPS:
            logger.warning(
                "Risk parity: degenerate portfolio variance (%s); returning current weights",
                portfolio_variance,
            )
            return weights

        marginal_risk = np.dot(covariance_matrix, weights)
        risk_contributions = weights * marginal_risk / portfolio_variance

        target_risk = 1.0 / n_assets
        scaling_factors = np.clip(target_risk / np.maximum(risk_contributions, VOL_FLOOR_EPS), 0.1, 10.0)
        new_weights = weights * scaling_factors
        new_weights = new_weights / np.sum(new_weights)

        weight_change = float(np.max(np.abs(new_weights - weights)))
        weights = new_weights
        if weight_change < tolerance:
            converged = True
            break

    if not converged:
        logger.warning(
            "Risk parity did not converge within %d iterations "
            "(last max weight change kept for reference); returning normalized weights",
            max_iterations,
        )

    return weights


def calculate_maximum_sharpe_weights(
    expected_returns: np.ndarray,
    covariance_matrix: np.ndarray,
    risk_free_rate: float,
) -> np.ndarray:
    try:
        excess_returns = np.asarray(expected_returns - risk_free_rate, dtype=np.float64)
        inv_cov_matrix = np.linalg.inv(covariance_matrix)
        optimal_weights = np.asarray(np.dot(inv_cov_matrix, excess_returns), dtype=np.float64)
        optimal_weights = optimal_weights / np.sum(optimal_weights)
        return optimal_weights
    except np.linalg.LinAlgError:
        logger.warning("Max Sharpe allocation fallback: singular covariance matrix -> equal weights")
        return calculate_equal_weights(len(expected_returns))


def calculate_minimum_variance_weights(covariance_matrix: np.ndarray) -> np.ndarray:
    try:
        n_assets = covariance_matrix.shape[0]
        ones_vector = np.ones((n_assets, 1))
        inv_cov_matrix = np.linalg.inv(covariance_matrix)

        numerator = np.dot(inv_cov_matrix, ones_vector)
        denominator = np.dot(ones_vector.T, np.dot(inv_cov_matrix, ones_vector))

        optimal_weights = (numerator / denominator).flatten()
        return optimal_weights
    except np.linalg.LinAlgError:
        logger.warning("Min Variance allocation fallback: singular covariance matrix -> equal weights")
        return calculate_equal_weights(covariance_matrix.shape[0])


_BOUNDS_MAX_ITERATIONS = 500
_BOUNDS_TOLERANCE = 1e-9


def _project_onto_simplex(vector: np.ndarray) -> np.ndarray:
    """Exact Euclidean projection onto the probability simplex (sum==1, w>=0)."""
    size = vector.size
    ordered = np.sort(vector)[::-1]
    cumulative = np.cumsum(ordered)
    index_range = np.arange(1, size + 1)
    condition = ordered * index_range > (cumulative - 1.0)
    rho = np.nonzero(condition)[0][-1]
    theta = (cumulative[rho] - 1.0) / (rho + 1)
    return np.maximum(vector - theta, 0.0)


def apply_weight_constraints(weights: np.ndarray, min_weight: float, max_weight: float) -> np.ndarray:
    """Enforce min/max bounds simultaneously with sum(weight)==1 (C4).

    Uses Dykstra's alternating projection onto the intersection of three
    convex sets — the probability simplex plus the two half-spaces imposed
    by the bounds. Convergence to the unique feasible region is guaranteed;
    raises ValueError when that intersection is empty (bounds infeasible for
    the asset count) or if the numerical verification at the end fails.
    """
    w = np.asarray(weights, dtype=np.float64).copy()
    n_assets = w.size

    if n_assets * min_weight > 1.0 + _BOUNDS_TOLERANCE or n_assets * max_weight < 1.0 - _BOUNDS_TOLERANCE:
        raise ValueError(
            f"Bounds infeasible for {n_assets} assets: need n*min<=1<=n*max "
            f"(n*min={n_assets * min_weight:.4f}, n*max={n_assets * max_weight:.4f}). "
            "Adjust minimum/maximum_single_asset_weight or the universe size."
        )

    # Working copy starts pre-normalized on the simplex.
    x = _project_onto_simplex(np.maximum(w, 0.0))

    # Dykstra correction accumulators per constraint set.
    p_min = np.zeros_like(x)
    p_max = np.zeros_like(x)
    p_sim = np.zeros_like(x)

    converged = False
    for _ in range(_BOUNDS_MAX_ITERATIONS):
        previous_x = x.copy()

        # Stage 1 — projection onto {w >= min_weight}:
        u_min = x + p_min
        v_min = np.maximum(u_min, min_weight)
        p_min = u_min - v_min

        # Stage 2 — projection onto {w <= max_weight}:
        u_max = v_min + p_max
        v_max = np.minimum(u_max, max_weight)
        p_max = u_max - v_max

        # Stage 3 — projection onto the probability simplex:
        u_sim = v_max + p_sim
        v_sim = _project_onto_simplex(u_sim)
        p_sim = u_sim - v_sim

        x = v_sim

        shift = float(np.max(np.abs(x - previous_x)))
        if shift < _BOUNDS_TOLERANCE / 10.0:
            converged = True
            break

    if not converged:
        logger.warning(
            "Weight-constraint projections did not converge within %d cycles "
            "(shift threshold %.1e)",
            _BOUNDS_MAX_ITERATIONS,
            _BOUNDS_TOLERANCE / 10.0,
        )

    # Hard final verification — never return silent violations.
    total = float(x.sum())
    if abs(total - 1.0) > _BOUNDS_TOLERANCE:
        raise ValueError(f"Constraint solver failed to normalize weights (sum={total:.12f})")
    violations = [
        i for i in range(n_assets)
        if x[i] < min_weight - _BOUNDS_TOLERANCE or x[i] > max_weight + _BOUNDS_TOLERANCE
    ]
    if violations:
        raise ValueError(
            f"Constraint solver left bounds violated at indices {violations}: {x}"
        )

    return x


def calculate_optimal_portfolio_weights(
    optimal_portfolio: dict,
    correlation_matrix: np.ndarray,
    full_covariance_matrix: np.ndarray,
    all_filtered_metrics: dict,
    config: PortfolioConfig,
) -> dict:
    """Dispatch to configured weighting method and return `{ticker: weight}`.

    Singular-matrix cases in analytic methods fall back to equal weights.
    """

    _ = correlation_matrix  # kept for backward-compatible signature

    logger.info(
        "Allocating portfolio weights: selected_assets=%d method=%s",
        len(optimal_portfolio),
        config.weight_allocation_method,
    )

    if len(optimal_portfolio) == 0:
        logger.warning("Weight allocation skipped: no selected assets")
        return {}

    if len(optimal_portfolio) == 1:
        ticker = list(optimal_portfolio.keys())[0]
        logger.info("Single asset selected: assigning full weight to %s", ticker)
        return {ticker: 1.0}

    portfolio_cov_matrix = create_portfolio_covariance_matrix(
        optimal_portfolio,
        full_covariance_matrix,
        all_filtered_metrics,
    )

    portfolio_tickers = list(optimal_portfolio.keys())
    expected_returns = np.array([optimal_portfolio[ticker]["annual_return"] for ticker in portfolio_tickers])
    asset_volatility = np.array([optimal_portfolio[ticker]["annual_volatility"] for ticker in portfolio_tickers])

    if config.weight_allocation_method == "equal":
        weights = calculate_equal_weights(len(portfolio_tickers))
    elif config.weight_allocation_method == "inverse_volatility":
        weights = calculate_inverse_volatility_weights(asset_volatility)
    elif config.weight_allocation_method == "risk_parity":
        weights = calculate_risk_parity_weights(portfolio_cov_matrix)
    elif config.weight_allocation_method == "max_sharpe":
        weights = calculate_maximum_sharpe_weights(expected_returns, portfolio_cov_matrix, config.risk_free_rate)
    elif config.weight_allocation_method == "min_variance":
        weights = calculate_minimum_variance_weights(portfolio_cov_matrix)
    else:
        # Unreachable by construction contract: PortfolioConfig validates the
        # method against WEIGHT_ALLOCATION_METHODS at construction time.
        raise ValueError(
            f"Unvalidated allocation method reached dispatch: '{config.weight_allocation_method}'"
        )

    weights = apply_weight_constraints(
        weights,
        config.minimum_single_asset_weight,
        config.maximum_single_asset_weight,
    )

    portfolio_weights = {ticker: weight for ticker, weight in zip(portfolio_tickers, weights)}
    logger.info("Weight allocation complete: assets=%d", len(portfolio_weights))
    return portfolio_weights


