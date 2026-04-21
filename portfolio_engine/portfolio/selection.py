"""Asset filtering and diversified candidate selection."""

import logging
import numpy as np
from numba import jit

from ..core.config import PortfolioConfig
from ..core.metrics import compute_correlation_distance_matrix


logger = logging.getLogger(__name__)


def apply_asset_filters(
    asset_metrics: dict,
    closing_prices: dict,
    minimum_sharpe: float = None,
    maximum_volatility: float = None,
):
    """Apply basic Sharpe/volatility screening before correlation clustering."""

    if minimum_sharpe is None and maximum_volatility is None:
        logger.info("Asset filters skipped: no thresholds provided")
        return asset_metrics.copy(), closing_prices.copy()

    logger.info(
        "Applying asset filters: input_assets=%d min_sharpe=%s max_volatility=%s",
        len(asset_metrics),
        minimum_sharpe,
        maximum_volatility,
    )

    filtered_metrics = {}
    filtered_prices = {}

    for ticker, metrics in asset_metrics.items():
        if minimum_sharpe is not None and metrics["sharpe_ratio"] < minimum_sharpe:
            continue

        if maximum_volatility is not None and metrics["annual_volatility"] > maximum_volatility:
            continue

        filtered_metrics[ticker] = metrics
        filtered_prices[ticker] = closing_prices[ticker]

    logger.info("Asset filters complete: kept=%d rejected=%d", len(filtered_metrics), len(asset_metrics) - len(filtered_metrics))
    return filtered_metrics, filtered_prices


@jit(nopython=True, cache=True)
def perform_hierarchical_clustering(distance_matrix: np.ndarray, distance_threshold: float) -> np.ndarray:
    """Greedy agglomerative clustering using a fixed distance threshold.

    The algorithm repeatedly merges the closest pair of different clusters.
    """

    matrix_size = distance_matrix.shape[0]
    cluster_assignments = np.arange(matrix_size, dtype=np.int32)
    clustering_changed = True

    while clustering_changed:
        clustering_changed = False
        minimum_distance = distance_threshold + 1.0
        merge_asset_i, merge_asset_j = -1, -1

        for i in range(matrix_size):
            for j in range(i + 1, matrix_size):
                if cluster_assignments[i] != cluster_assignments[j] and distance_matrix[i, j] < minimum_distance:
                    minimum_distance = distance_matrix[i, j]
                    merge_asset_i, merge_asset_j = i, j

        if minimum_distance <= distance_threshold and merge_asset_i != -1:
            cluster_to_merge = cluster_assignments[merge_asset_j]
            target_cluster = cluster_assignments[merge_asset_i]
            for k in range(matrix_size):
                if cluster_assignments[k] == cluster_to_merge:
                    cluster_assignments[k] = target_cluster
            clustering_changed = True

    return cluster_assignments


def select_optimal_diversified_portfolio(
    correlation_matrix: np.ndarray,
    asset_metrics: dict,
    config: PortfolioConfig,
) -> dict:
    """Pick one representative asset per cluster using a weighted composite score.

    Score = Sharpe contribution + diversification contribution - volatility penalty.
    """

    ticker_list = list(asset_metrics.keys())
    number_of_assets = len(ticker_list)

    logger.info("Selecting diversified portfolio: candidate_assets=%d", number_of_assets)

    if number_of_assets != correlation_matrix.shape[0]:
        raise ValueError("Number of assets doesn't match correlation matrix size")
    if number_of_assets <= 1:
        return asset_metrics

    correlation_distance_threshold = 1.0 - config.maximum_correlation_threshold
    distance_matrix = compute_correlation_distance_matrix(correlation_matrix)
    cluster_labels = perform_hierarchical_clustering(distance_matrix, correlation_distance_threshold)

    asset_clusters = {}
    for asset_index, ticker in enumerate(ticker_list):
        cluster_id = cluster_labels[asset_index]
        if cluster_id not in asset_clusters:
            asset_clusters[cluster_id] = []
        asset_clusters[cluster_id].append((asset_index, ticker))

    selected_portfolio = {}

    for cluster_id, assets_in_cluster in asset_clusters.items():
        best_asset_ticker = None
        highest_composite_score = -np.inf

        for asset_index, ticker in assets_in_cluster:
            metrics = asset_metrics[ticker]

            sharpe_component = metrics["sharpe_ratio"] * config.sharpe_weight

            volatility_penalty = min(
                metrics["annual_volatility"] / config.volatility_penalty_scale,
                config.max_volatility_penalty_multiplier,
            ) * config.volatility_penalty_weight

            cross_cluster_correlation_sum = 0.0
            other_assets_count = 0
            for other_cluster_id, other_cluster_assets in asset_clusters.items():
                if other_cluster_id != cluster_id:
                    for other_asset_index, _ in other_cluster_assets:
                        cross_cluster_correlation_sum += abs(correlation_matrix[asset_index, other_asset_index])
                        other_assets_count += 1

            diversification_component = (
                1.0 - (cross_cluster_correlation_sum / other_assets_count if other_assets_count > 0 else 0.0)
            ) * config.diversification_weight

            composite_score = sharpe_component + diversification_component - volatility_penalty

            if composite_score > highest_composite_score:
                highest_composite_score = composite_score
                best_asset_ticker = ticker

        if best_asset_ticker:
            selected_portfolio[best_asset_ticker] = asset_metrics[best_asset_ticker]

    logger.info(
        "Diversified selection complete: clusters=%d selected_assets=%d",
        len(asset_clusters),
        len(selected_portfolio),
    )
    return selected_portfolio


