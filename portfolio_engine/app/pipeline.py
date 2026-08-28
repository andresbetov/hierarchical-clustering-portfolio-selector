"""Top-level orchestration of the portfolio analysis workflow."""

import logging
from pathlib import Path

import numpy as np

from ..core.config import PortfolioConfig
from ..core.metrics import (
    align_prices_to_common_calendar,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    construct_returns_matrix,
)
from ..portfolio.allocation import (
    calculate_optimal_portfolio_weights,
    calculate_optimal_portfolio_weights_hrp,
    create_portfolio_covariance_matrix,
)
from ..portfolio.selection import apply_asset_filters, select_optimal_diversified_portfolio
from ..viz.reporting import (
    finalize_report_show,
    plot_asset_metrics_comparison,
    plot_correlation_covariance_matrices,
    plot_correlation_heatmap,
    plot_filtering_analysis,
    plot_historical_prices,
    plot_optimal_portfolio_analysis,
    plot_risk_return_scatter,
)

logger = logging.getLogger(__name__)


CHART_FILENAMES = {
    "historical_prices": "historical_price_trends_normalized.png",
    "risk_return_scatter": "asset_risk_return_profile.png",
    "asset_metrics_comparison": "asset_metrics_comparison_dashboard.png",
    "correlation_covariance_matrices": "asset_relationship_matrices.png",
    "filtering_analysis": "asset_filtering_effects.png",
    "filtered_correlation_heatmap": "filtered_assets_correlation_heatmap.png",
    "optimal_portfolio_analysis": "optimal_portfolio_allocation_summary.png",
}


def main(
    ticker_symbols: list,
    config: PortfolioConfig | None = None,
    provider=None,
):
    """Run the core pipeline: fetch -> filter -> align -> cluster -> allocate.

    `provider` is an optional MarketDataProvider (structural protocol); when
    omitted a YFinanceProvider is constructed. Orchestration never imports
    transport modules directly (M3 seam).

    Returns raw metrics, filtered universe, selected portfolio, weights and matrices
    so callers can build custom reports without rerunning computations.
    """
    if config is None:
        config = PortfolioConfig()
    if provider is None:
        from ..data.provider import YFinanceProvider

        provider = YFinanceProvider()

    logger.info(
        "Pipeline started: tickers=%d provider=%s",
        len(ticker_symbols),
        type(provider).__name__,
    )

    asset_metrics, closing_prices, price_dates = provider.fetch_metrics(
        ticker_symbols,
        config.risk_free_rate,
        config.lookback_years,
        config.trading_days_per_year,
    )

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

    # A3: multivariate stats must run on the common calendar (inner join),
    # otherwise rows of different trading days get compared silently.
    aligned_prices = align_prices_to_common_calendar(filtered_prices, price_dates)
    aligned_rows = len(next(iter(aligned_prices.values()))) if aligned_prices else 0
    logger.info(
        "Calendar alignment: tickers=%d common_rows=%d input_rows(first)=%d",
        len(aligned_prices),
        aligned_rows,
        len(filtered_prices[next(iter(filtered_prices))]) if filtered_prices else 0,
    )

    daily_returns_matrix = construct_returns_matrix(aligned_prices)
    correlation_matrix = calculate_correlation_matrix(daily_returns_matrix)
    covariance_matrix = calculate_covariance_matrix(daily_returns_matrix)

    if config.weight_allocation_method == "hrp":
        # End-to-end hierarchical path (ADR 003): every filtered asset is
        # allocated via linkage -> quasi-diag -> recursive bisection. The
        # legacy two-stage scoring/pruning flow is bypassed entirely.
        portfolio_weights = calculate_optimal_portfolio_weights_hrp(
            filtered_metrics,
            covariance_matrix,
            config,
        )
        optimal_portfolio = dict(filtered_metrics)
    else:
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
    config: PortfolioConfig | None = None,
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

    (
        all_metrics,
        filtered_metrics,
        optimal_portfolio,
        portfolio_weights,
        corr_matrix,
        covariance_matrix,
        historical_prices,
        price_dates,
    ) = main(ticker_symbols, config)

    logger.info("Generating complete portfolio analysis report")

    logger.info("Rendering chart: historical prices")
    plot_historical_prices(
        historical_prices,
        price_dates,
        f"charts/{CHART_FILENAMES['historical_prices']}" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: risk-return scatter")
    plot_risk_return_scatter(
        all_metrics,
        config,
        f"charts/{CHART_FILENAMES['risk_return_scatter']}" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: asset metrics comparison")
    plot_asset_metrics_comparison(
        all_metrics,
        f"charts/{CHART_FILENAMES['asset_metrics_comparison']}" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: correlation and covariance matrices")
    all_tickers = list(all_metrics.keys())
    # Rebuild the full-universe matrices here so the report can compare the original asset set,
    # not only the filtered subset used for selection.
    all_prices_dict = {ticker: historical_prices[ticker] for ticker in all_tickers if ticker in historical_prices}
    all_returns_matrix = construct_returns_matrix(all_prices_dict)
    all_corr_matrix = calculate_correlation_matrix(all_returns_matrix)
    all_cov_matrix = calculate_covariance_matrix(all_returns_matrix)

    plot_correlation_covariance_matrices(
        all_corr_matrix,
        all_cov_matrix,
        all_tickers,
        f"charts/{CHART_FILENAMES['correlation_covariance_matrices']}" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: filtering analysis")
    plot_filtering_analysis(
        all_metrics,
        filtered_metrics,
        config,
        f"charts/{CHART_FILENAMES['filtering_analysis']}" if save_plots else None,
        show_plot=show_plots,
    )

    logger.info("Rendering chart: filtered assets correlation")
    filtered_tickers = list(filtered_metrics.keys())
    if len(filtered_tickers) > 1:
        plot_correlation_heatmap(
            corr_matrix,
            filtered_tickers,
            f"charts/{CHART_FILENAMES['filtered_correlation_heatmap']}" if save_plots else None,
            show_plot=show_plots,
        )

    if optimal_portfolio and portfolio_weights:
        logger.info("Rendering chart: optimal portfolio analysis")
        # feat-028: legacy routes can select M < N assets; the report must
        # receive the covariance sliced to the exact selected subset (same
        # ticker order as the weights), never the NxN filtered matrix.
        portfolio_covariance = create_portfolio_covariance_matrix(
            optimal_portfolio,
            covariance_matrix,
            filtered_metrics,
        )
        plot_optimal_portfolio_analysis(
            optimal_portfolio,
            portfolio_weights,
            config,
            f"charts/{CHART_FILENAMES['optimal_portfolio_analysis']}" if save_plots else None,
            show_plot=show_plots,
            covariance_matrix=portfolio_covariance,
        )
    else:
        logger.warning("Skipping optimal portfolio chart: no selected assets")

    # Single lifecycle decision point: display interactively when requested
    # (and possible), otherwise close everything deterministically.
    finalize_report_show(show_plots)

    logger.info(
        "Report generated: plots=%d analyzed=%d filtered=%d final_portfolio=%d",
        7,
        len(all_tickers),
        len(filtered_tickers),
        len(optimal_portfolio),
    )

    return all_metrics, filtered_metrics, optimal_portfolio, portfolio_weights


