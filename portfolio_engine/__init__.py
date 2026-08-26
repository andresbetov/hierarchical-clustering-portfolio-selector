"""Hierarchical Clustering Portfolio Selector — quantitative pipeline.

Builds equity portfolios through explicit, reproducible rules:
adjusted-price ingestion (batched, cached upstream boundary), calendar
alignment, correlation-based clustering with a SIGNED distance metric,
Hierarchical Risk Parity allocation (default; no matrix inversion) with
concentration bounds enforced by cyclic projection, and optional
walk-forward out-of-sample validation.

Methodological decisions are versioned as ADRs under docs/adr/.
Quick start: `uv sync && uv run portfolio-run` over config/universe.yaml.
"""

from .app.pipeline import generate_complete_analysis_report, main
from .core.config import PortfolioConfig
from .core.logging_utils import configure_logging
from .core.metrics import (
    align_prices_to_common_calendar,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_sharpe_ratio,
    compute_correlation_distance_matrix,
    compute_logarithmic_returns,
    construct_returns_matrix,
)
from .data.data_fetch import download_and_calculate_metrics
from .data.provider import MarketDataProvider, YFinanceProvider
from .data.universe import load_universe
from .portfolio.allocation import (
    apply_weight_constraints,
    calculate_equal_weights,
    calculate_inverse_volatility_weights,
    calculate_maximum_sharpe_weights,
    calculate_minimum_variance_weights,
    calculate_optimal_portfolio_weights,
    calculate_optimal_portfolio_weights_hrp,
    calculate_portfolio_return,
    calculate_portfolio_variance,
    calculate_risk_parity_weights,
    create_portfolio_covariance_matrix,
)
from .portfolio.hrp import calculate_hrp_weights
from .portfolio.selection import (
    apply_asset_filters,
    perform_hierarchical_clustering,
    select_optimal_diversified_portfolio,
)
from .validation.walk_forward import WalkForwardReport, walk_forward_evaluate
from .viz.reporting import (
    plot_asset_metrics_comparison,
    plot_correlation_covariance_matrices,
    plot_correlation_heatmap,
    plot_filtering_analysis,
    plot_historical_prices,
    plot_optimal_portfolio_analysis,
    plot_risk_return_scatter,
    print_correlation_matrix,
    print_covariance_matrix,
    print_portfolio_summary,
)

__all__ = [
    "PortfolioConfig",
    "MarketDataProvider",
    "YFinanceProvider",
    "download_and_calculate_metrics",
    "load_universe",
    "compute_logarithmic_returns",
    "calculate_annualized_return",
    "calculate_annualized_volatility",
    "calculate_sharpe_ratio",
    "calculate_correlation_matrix",
    "calculate_covariance_matrix",
    "construct_returns_matrix",
    "align_prices_to_common_calendar",
    "compute_correlation_distance_matrix",
    "apply_asset_filters",
    "perform_hierarchical_clustering",
    "select_optimal_diversified_portfolio",
    "create_portfolio_covariance_matrix",
    "calculate_portfolio_variance",
    "calculate_portfolio_return",
    "calculate_equal_weights",
    "calculate_inverse_volatility_weights",
    "calculate_risk_parity_weights",
    "calculate_maximum_sharpe_weights",
    "calculate_minimum_variance_weights",
    "apply_weight_constraints",
    "calculate_optimal_portfolio_weights",
    "calculate_optimal_portfolio_weights_hrp",
    "calculate_hrp_weights",
    "walk_forward_evaluate",
    "WalkForwardReport",
    "plot_historical_prices",
    "plot_risk_return_scatter",
    "plot_correlation_covariance_matrices",
    "plot_correlation_heatmap",
    "plot_asset_metrics_comparison",
    "plot_filtering_analysis",
    "plot_optimal_portfolio_analysis",
    "print_correlation_matrix",
    "print_covariance_matrix",
    "print_portfolio_summary",
    "main",
    "generate_complete_analysis_report",
    "configure_logging",
]
