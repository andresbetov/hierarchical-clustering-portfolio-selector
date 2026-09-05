"""Hierarchical Risk Parity allocation (De Prado 2016; Palomar ch.12.3).

Three canonical steps over the filtered universe:
  1. tree clustering via scipy linkage on the (signed) correlation distance
  2. quasi-diagonalization — leaf order that clusters similar assets adjacently
  3. recursive bisection allocating capital by cluster inverse-variance

Never inverts the covariance matrix: only diagonal slices feed the
inverse-variance intermediate portfolios, which is precisely why HRP stays
stable where quadratic optimizers explode (C1 resolution).
"""

import logging

import numpy as np
from scipy.cluster.hierarchy import linkage

logger = logging.getLogger(__name__)

LINKAGE_METHODS = ("single", "ward", "average")


def _leaf_order(linkage_matrix: np.ndarray, number_of_leaves: int) -> list[int]:
    """Expand the scipy linkage tree into its quasi-diagonal leaf order (iterative)."""
    if number_of_leaves <= 0:
        return []
    if number_of_leaves == 1:
        return [0]
    # Iterative DFS to avoid recursion limit on chain-like trees (~n depth).
    root = 2 * number_of_leaves - 2
    stack: list[int] = [root]
    order: list[int] = []
    while stack:
        cluster_id = stack.pop()
        if cluster_id < number_of_leaves:
            order.append(cluster_id)
        else:
            row = linkage_matrix[cluster_id - number_of_leaves]
            # Push right then left so left is processed first (preorder).
            stack.append(int(row[1]))
            stack.append(int(row[0]))
    return order


def _cluster_inverse_variance_portfolios(cov_slice: np.ndarray) -> float:
    """Variance of the inverse-variance portfolio over a cov slice."""
    diagonal = np.diag(cov_slice).copy()
    # Floor degenerate variances so a zero-variance asset cannot explode IVP weights.
    floor = max(float(diagonal.min()), 1e-18)
    diagonal = np.maximum(diagonal, floor)
    inverse_variance_weights = 1.0 / diagonal
    inverse_variance_weights /= inverse_variance_weights.sum()
    variance = float(inverse_variance_weights @ cov_slice @ inverse_variance_weights)
    return variance


def build_hrp_linkage(covariance_matrix: np.ndarray, linkage_method: str = "single") -> np.ndarray:
    """Build HRP linkage matrix from covariance (single source of distance/linkage).

    Reuses the signed distance ``sqrt(0.5*(1-corr))`` via ``_correlations_from_cov``.
    Validates ``linkage_method`` before touching scipy and mirrors the guards of
    ``calculate_hrp_weights`` (square, finite, symmetric, diag>0). Requires ``n>=2``.
    """
    cov = np.asarray(covariance_matrix, dtype=np.float64)

    if linkage_method not in LINKAGE_METHODS:
        raise ValueError(
            f"Unknown linkage_method '{linkage_method}'; allowed: {list(LINKAGE_METHODS)}"
        )

    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError(f"Covariance must be square, got shape {cov.shape}")
    if not np.all(np.isfinite(cov)):
        raise ValueError("Covariance contains non-finite entries; upstream guards failed")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("Covariance is not symmetric")
    if np.any(np.diag(cov) <= 0):
        raise ValueError("Covariance has non-positive variance on the diagonal")

    number_of_assets = cov.shape[0]
    if number_of_assets < 2:
        raise ValueError(f"Linkage requires at least 2 assets, got {number_of_assets}")

    distance = np.sqrt(np.maximum(0.5 * (1.0 - _correlations_from_cov(cov)), 0.0))
    np.fill_diagonal(distance, 0.0)

    from scipy.spatial.distance import squareform

    condensed = squareform(distance, checks=False)
    return linkage(condensed, method=linkage_method)


def calculate_hrp_weights(covariance_matrix: np.ndarray, linkage_method: str = "single") -> np.ndarray:
    """Compute HRP weights for assets ordered as covariance_matrix columns.

    `linkage_method` (ADR 006) selects the scipy hierarchical clustering
    method: "single" (De Prado original, default — snapshot-compatible),
    "ward" or "average". Deterministic; strictly positive weights summing
    to exactly 1 before any downstream bound constraints are applied.

    Raises ValueError on non-finite/asymmetric inputs (C3 contract: fail loud)
    and on unknown linkage methods (before touching scipy).
    """
    cov = np.asarray(covariance_matrix, dtype=np.float64)

    if linkage_method not in LINKAGE_METHODS:
        raise ValueError(
            f"Unknown linkage_method '{linkage_method}'; allowed: {list(LINKAGE_METHODS)}"
        )

    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise ValueError(f"Covariance must be square, got shape {cov.shape}")
    if not np.all(np.isfinite(cov)):
        raise ValueError("Covariance contains non-finite entries; upstream guards failed")
    if not np.allclose(cov, cov.T, atol=1e-10):
        raise ValueError("Covariance is not symmetric")
    if np.any(np.diag(cov) <= 0):
        raise ValueError("Covariance has non-positive variance on the diagonal")

    number_of_assets = cov.shape[0]

    if number_of_assets == 1:
        return np.array([1.0])

    if number_of_assets == 2:
        # No clustering needed: bisection degenerates to the two singleton
        # clusters and alpha reduces to plain inverse-variance across them.
        variances = np.diag(cov)
        weights = np.array([variances[1], variances[0]]) / variances.sum()
        return weights

    linkage_matrix = build_hrp_linkage(cov, linkage_method=linkage_method)

    sort_index = _leaf_order(linkage_matrix, number_of_assets)
    sorted_tickers_cov = cov[np.ix_(sort_index, sort_index)]

    weights_sorted = np.ones(number_of_assets)
    cluster_lists = [list(range(number_of_assets))]

    while cluster_lists:
        # Bisection of every current cluster into halves:
        cluster_lists = [
            items[j:k]
            for items in cluster_lists
            for j, k in ((0, len(items) // 2), (len(items) // 2, len(items)))
            if len(items) > 1
        ]
        for i in range(0, len(cluster_lists), 2):
            left_items = cluster_lists[i]
            right_items = cluster_lists[i + 1]
            variance_left = _cluster_inverse_variance_portfolios(sorted_tickers_cov[np.ix_(left_items, left_items)])
            variance_right = _cluster_inverse_variance_portfolios(sorted_tickers_cov[np.ix_(right_items, right_items)])

            alpha_left = 1.0 - variance_left / (variance_left + variance_right)
            weights_sorted[left_items] *= alpha_left
            weights_sorted[right_items] *= 1.0 - alpha_left

    # Un-sort back to the caller's original column order and normalize.
    weights = np.empty_like(weights_sorted)
    for position, original_index in enumerate(sort_index):
        weights[original_index] = weights_sorted[position]

    total = weights.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValueError(f"HRP produced invalid weight mass ({total})")
    return weights / total


def _correlations_from_cov(cov: np.ndarray) -> np.ndarray:
    standard_deviations = np.sqrt(np.diag(cov))
    outer_std = np.outer(standard_deviations, standard_deviations)
    with np.errstate(divide="ignore", invalid="ignore"):
        correlations = cov / outer_std
    correlations = np.clip(correlations, -1.0, 1.0)
    np.fill_diagonal(correlations, 1.0)
    return correlations
