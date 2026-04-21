"""Top-level orchestration of the portfolio analysis workflow."""

import logging
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from ..portfolio.allocation import calculate_optimal_portfolio_weights
from ..core.config import PortfolioConfig
from ..data.data_fetch import download_and_calculate_metrics
from ..core.metrics import calculate_correlation_matrix, calculate_covariance_matrix, construct_returns_matrix
from ..viz.reporting import (
    plot_asset_metrics_comparison,
    plot_correlation_covariance_matrices,
    plot_correlation_heatmap,
    plot_filtering_analysis,
    plot_historical_prices,
    plot_optimal_portfolio_analysis,
    plot_risk_return_scatter,
)
from ..portfolio.selection import apply_asset_filters, select_optimal_diversified_portfolio


logger = logging.getLogger(__name__)


def main(ticker_symbols: list, config: PortfolioConfig = None):
    """Run the core pipeline: download -> filter -> stats -> select -> allocate.

    Returns raw metrics, filtered universe, selected portfolio, weights and matrices
    so callers can build custom reports without rerunning computations.
    """

    if config is None:
        config = PortfolioConfig()

    logger.info("Pipeline started: tickers=%d", len(ticker_symbols))

    asset_metrics, closing_prices, price_dates = download_and_calculate_metrics(ticker_symbols, config.risk_free_rate)

    filtered_metrics, filtered_prices = apply_asset_filters(
        asset_metrics,
        closing_prices,
        config.minimum_sharpe_threshold,
        config.maximum_volatility_threshold,
    )

    logger.info("Pipeline filtering summary: input=%d filtered=%d", len(asset_metrics), len(filtered_metrics))

    if not filtered_metrics:
        logger.warning("No assets left after filtering; skipping correlation/selection/allocation")
        empty_matrix = np.empty((0, 0), dtype=np.float64)
        return (
            asset_metrics,
            filtered_metrics,
            {},
            {},
            empty_matrix,
            empty_matrix,
            closing_prices,
            price_dates,
        )

    daily_returns_matrix = construct_returns_matrix(filtered_prices)
    correlation_matrix = calculate_correlation_matrix(daily_returns_matrix)
    covariance_matrix = calculate_covariance_matrix(daily_returns_matrix)

    optimal_portfolio = select_optimal_diversified_portfolio(correlation_matrix, filtered_metrics, config)

    portfolio_weights = calculate_optimal_portfolio_weights(
        optimal_portfolio,
        correlation_matrix,
        covariance_matrix,
        filtered_metrics,
        config,
    )

    logger.info("Pipeline complete: selected_assets=%d", len(optimal_portfolio))

    return (
        asset_metrics,
        filtered_metrics,
        optimal_portfolio,
        portfolio_weights,
        correlation_matrix,
        covariance_matrix,
        closing_prices,
        price_dates,
    )


def generate_complete_analysis_report(
    ticker_symbols: list,
    config: PortfolioConfig = None,
    save_plots: bool = False,
    show_plots: bool = False,
):
    """Run the pipeline and emit the standard 7-plot analysis report.

    Args:
        save_plots: when True, writes PNG files under `charts/` paths.
        show_plots: when True, opens plot windows after generating all figures.
    """

    if config is None:
        config = PortfolioConfig()

    if save_plots:
        Path("charts").mkdir(parents=True, exist_ok=True)
        logger.info("Charts directory ready: path=charts")

    all_metrics, filtered_metrics, optimal_portfolio, portfolio_weights, corr_matrix, _, historical_prices, price_dates = main(
        ticker_symbols,
        config,
    )

    logger.info("Generating complete portfolio analysis report")

    logger.info("Rendering chart: historical prices")
    plot_historical_prices(
        historical_prices,
        price_dates,
        "charts/historical_prices.png" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: risk-return scatter")
    plot_risk_return_scatter(
        all_metrics,
        config,
        "charts/risk_return_analysis.png" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: asset metrics comparison")
    plot_asset_metrics_comparison(
        all_metrics,
        "charts/asset_metrics_comparison.png" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: correlation and covariance matrices")
    all_tickers = list(all_metrics.keys())
    all_prices_dict = {ticker: historical_prices[ticker] for ticker in all_tickers if ticker in historical_prices}
    all_returns_matrix = construct_returns_matrix(all_prices_dict)
    all_corr_matrix = calculate_correlation_matrix(all_returns_matrix)
    all_cov_matrix = calculate_covariance_matrix(all_returns_matrix)

    plot_correlation_covariance_matrices(
        all_corr_matrix,
        all_cov_matrix,
        all_tickers,
        "charts/correlation_covariance_matrices.png" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: filtering analysis")
    plot_filtering_analysis(
        all_metrics,
        filtered_metrics,
        config,
        "charts/filtering_analysis.png" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: filtered assets correlation")
    filtered_tickers = list(filtered_metrics.keys())
    if len(filtered_tickers) > 1:
        plot_correlation_heatmap(
            corr_matrix,
            filtered_tickers,
            "charts/filtered_correlation_heatmap.png" if save_plots else None,
            show_plot=show_plots,
        )

    if optimal_portfolio and portfolio_weights:
        logger.info("Rendering chart: optimal portfolio analysis")
        plot_optimal_portfolio_analysis(
            optimal_portfolio,
            portfolio_weights,
            config,
            "charts/optimal_portfolio_analysis.png" if save_plots else None,
            show_plot=show_plots,
        )
    else:
        logger.warning("Skipping optimal portfolio chart: no selected assets")

    if show_plots:
        # Keep windows open only once after all figures are created.
        plt.show()

    logger.info(
        "Report generated: plots=%d analyzed=%d filtered=%d final_portfolio=%d",
        7,
        len(all_tickers),
        len(filtered_tickers),
        len(optimal_portfolio),
    )

    return all_metrics, filtered_metrics, optimal_portfolio, portfolio_weights


