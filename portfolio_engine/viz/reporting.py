"""Visualization and text-report utilities for portfolio outputs."""

import logging
import os
import sys

import matplotlib

from ..core.config import PortfolioConfig
from ..core.metrics import VOL_FLOOR_EPS, risk_free_log_rate

logger = logging.getLogger(__name__)


def _resolve_backend(env: dict[str, str], platform: str) -> str | None:
    """Pick the matplotlib backend for the current environment.

    Returns "Agg" only when there is no display available, the user has NOT
    forced MPLBACKEND, and the platform cannot provide a native backend
    (non-macOS). Returns None when the environment already dictates one.
    """
    if env.get("MPLBACKEND"):
        return None
    if platform == "darwin":
        return None
    if env.get("DISPLAY"):
        return None
    return "Agg"


def _apply_backend_guard() -> None:
    """Force Agg before pyplot/seaborn get imported anywhere in the process.

    seaborn imports pyplot internally, so this must run before that import.
    """
    resolved = _resolve_backend(dict(os.environ), sys.platform)
    if resolved:
        logger.debug("Headless environment detected: forcing backend=%s", resolved)
        matplotlib.use(resolved)


_apply_backend_guard()

import matplotlib.pyplot as plt  # noqa: E402  (must run after backend guard)
import numpy as np  # noqa: E402  (grouped after guard: see matplotlib/seaborn)
import seaborn as sns  # noqa: E402  (seaborn pulls pyplot; guard must run first)


def finalize_report_show(show: bool) -> None:
    """Close or display all pending figures depending on the runtime mode.

    - show=False (batch/report mode): deterministic close of every figure.
    - show=True with an interactive backend: non-blocking pause so windows render.
    - show=True under a headless (Agg) backend: falls back to closing quietly,
      guaranteeing CI runs never hang or warn about interactivity.
    """
    if not show:
        plt.close("all")
        return

    if plt.get_backend().lower() == "agg":
        plt.close("all")
        return

    # Non-blocking per figure; caller can block once at the end if desired.
    plt.show(block=False)
    plt.pause(0.001)


def _finalize_plot(save_path: str | None = None, show_plot: bool = True):
    """Apply consistent save/show behavior for every chart.

    Deterministic lifecycle: figures are always closed when not requested to
    display; interactive backends get non-blocking shows. Under Agg the show
    branch is skipped entirely so CI never warns or hangs.
    """

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    if show_plot and plt.get_backend().lower() != "agg":
        # Non-blocking per figure; caller can block once at the end if desired.
        plt.show(block=False)
        plt.pause(0.001)
    else:
        plt.close()


def plot_historical_prices(
    historical_prices: dict,
    price_dates: dict,
    save_path: str | None = None,
    show_plot: bool = True,
):
    plt.figure(figsize=(15, 10))

    for ticker in historical_prices:
        if ticker in price_dates:
            dates = price_dates[ticker]
            prices = historical_prices[ticker]
            normalized_prices = prices / prices[0] * 100
            plt.plot(dates, normalized_prices, label=ticker, linewidth=2, alpha=0.8)

    plt.title("Historical Price Performance (Normalized to 100)", fontsize=16, fontweight="bold")
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Normalized Price", fontsize=12)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def plot_risk_return_scatter(
    asset_metrics: dict,
    config: PortfolioConfig,
    save_path: str | None = None,
    show_plot: bool = True,
):
    plt.figure(figsize=(12, 8))

    returns = [metrics["annual_return"] for metrics in asset_metrics.values()]
    volatilities = [metrics["annual_volatility"] for metrics in asset_metrics.values()]
    sharpe_ratios = [metrics["sharpe_ratio"] for metrics in asset_metrics.values()]
    tickers = list(asset_metrics.keys())

    scatter = plt.scatter(volatilities, returns, c=sharpe_ratios, s=100, cmap="RdYlGn", alpha=0.7, edgecolors="black")

    for i, ticker in enumerate(tickers):
        plt.annotate(
            ticker,
            (volatilities[i], returns[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontweight="bold",
        )

    plt.axhline(
        y=config.risk_free_rate_log,
        color="blue",
        linestyle="--",
        label=f"Risk-free rate log ({config.risk_free_rate_log:.2%})",
    )
    plt.axvline(
        x=config.maximum_volatility_threshold,
        color="red",
        linestyle="--",
        label=f"Max volatility ({config.maximum_volatility_threshold:.1%})",
    )

    plt.colorbar(scatter, label="Sharpe Ratio")
    plt.title("Risk-Return Analysis of All Assets", fontsize=16, fontweight="bold")
    plt.xlabel("Annual Volatility", fontsize=12)
    plt.ylabel("Annual Return", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def plot_correlation_covariance_matrices(
    correlation_matrix: np.ndarray,
    covariance_matrix: np.ndarray,
    asset_tickers: list,
    save_path: str | None = None,
    show_plot: bool = True,
):
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))

    mask_corr = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="RdBu_r",
        center=0,
        xticklabels=asset_tickers,
        yticklabels=asset_tickers,
        mask=mask_corr,
        square=True,
        linewidths=0.5,
        ax=axes[0],
        fmt=".3f",
        cbar_kws={"label": "Correlation Coefficient"},
    )
    axes[0].set_title("Asset Correlation Matrix", fontsize=14, fontweight="bold")
    axes[0].set_xlabel("Assets", fontsize=12)
    axes[0].set_ylabel("Assets", fontsize=12)

    mask_cov = np.tril(np.ones_like(covariance_matrix, dtype=bool))
    sns.heatmap(
        covariance_matrix,
        annot=True,
        cmap="viridis",
        xticklabels=asset_tickers,
        yticklabels=asset_tickers,
        mask=mask_cov,
        square=True,
        linewidths=0.5,
        ax=axes[1],
        fmt=".6f",
        cbar_kws={"label": "Covariance"},
    )
    axes[1].set_title("Asset Covariance Matrix", fontsize=14, fontweight="bold")
    axes[1].set_xlabel("Assets", fontsize=12)
    axes[1].set_ylabel("Assets", fontsize=12)

    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def plot_correlation_heatmap(
    correlation_matrix: np.ndarray,
    asset_tickers: list,
    save_path: str | None = None,
    show_plot: bool = True,
):
    plt.figure(figsize=(12, 10))

    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    sns.heatmap(
        correlation_matrix,
        annot=True,
        cmap="RdBu_r",
        center=0,
        xticklabels=asset_tickers,
        yticklabels=asset_tickers,
        mask=mask,
        square=True,
        linewidths=0.5,
    )

    plt.title("Asset Correlation Matrix", fontsize=16, fontweight="bold")
    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def plot_asset_metrics_comparison(asset_metrics: dict, save_path: str | None = None, show_plot: bool = True):
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    tickers = list(asset_metrics.keys())
    returns = [metrics["annual_return"] for metrics in asset_metrics.values()]
    volatilities = [metrics["annual_volatility"] for metrics in asset_metrics.values()]
    sharpe_ratios = [metrics["sharpe_ratio"] for metrics in asset_metrics.values()]

    axes[0, 0].bar(tickers, returns, color="skyblue", alpha=0.8)
    axes[0, 0].set_title("Annual Returns by Asset", fontweight="bold")
    axes[0, 0].set_ylabel("Annual Return")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].bar(tickers, volatilities, color="salmon", alpha=0.8)
    axes[0, 1].set_title("Annual Volatilities by Asset", fontweight="bold")
    axes[0, 1].set_ylabel("Annual Volatility")
    axes[0, 1].tick_params(axis="x", rotation=45)
    axes[0, 1].grid(True, alpha=0.3)

    colors = ["green" if sr > 0.5 else "orange" if sr > 0 else "red" for sr in sharpe_ratios]
    axes[1, 0].bar(tickers, sharpe_ratios, color=colors, alpha=0.8)
    axes[1, 0].set_title("Sharpe Ratios by Asset", fontweight="bold")
    axes[1, 0].set_ylabel("Sharpe Ratio")
    axes[1, 0].tick_params(axis="x", rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].axhline(y=0.5, color="black", linestyle="--", alpha=0.5, label="Min threshold")
    axes[1, 0].legend()

    axes[1, 1].scatter(volatilities, returns, s=100, alpha=0.7, c=sharpe_ratios, cmap="RdYlGn")
    for i, ticker in enumerate(tickers):
        axes[1, 1].annotate(
            ticker,
            (volatilities[i], returns[i]),
            xytext=(3, 3),
            textcoords="offset points",
            fontsize=8,
        )
    axes[1, 1].set_title("Risk-Return Efficiency", fontweight="bold")
    axes[1, 1].set_xlabel("Annual Volatility")
    axes[1, 1].set_ylabel("Annual Return")
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def plot_filtering_analysis(
    all_metrics: dict,
    filtered_metrics: dict,
    config: PortfolioConfig,
    save_path: str | None = None,
    show_plot: bool = True,
):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    all_tickers = list(all_metrics.keys())
    filtered_tickers = list(filtered_metrics.keys())
    rejected_tickers = [t for t in all_tickers if t not in filtered_tickers]

    sharpe_ratios = [all_metrics[ticker]["sharpe_ratio"] for ticker in all_tickers]
    colors = ["green" if ticker in filtered_tickers else "red" for ticker in all_tickers]

    axes[0].bar(all_tickers, sharpe_ratios, color=colors, alpha=0.8)
    axes[0].axhline(
        y=config.minimum_sharpe_threshold,
        color="black",
        linestyle="--",
        label=f"Min Sharpe ({config.minimum_sharpe_threshold})",
    )
    axes[0].set_title("Sharpe Ratio Filter", fontweight="bold")
    axes[0].set_ylabel("Sharpe Ratio")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    volatilities = [all_metrics[ticker]["annual_volatility"] for ticker in all_tickers]

    axes[1].bar(all_tickers, volatilities, color=colors, alpha=0.8)
    axes[1].axhline(
        y=config.maximum_volatility_threshold,
        color="black",
        linestyle="--",
        label=f"Max Volatility ({config.maximum_volatility_threshold:.1%})",
    )
    axes[1].set_title("Volatility Filter", fontweight="bold")
    axes[1].set_ylabel("Annual Volatility")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    result_counts = {"Passed": len(filtered_tickers), "Rejected": len(rejected_tickers)}

    axes[2].pie(
        result_counts.values(),
        labels=result_counts.keys(),
        autopct="%1.1f%%",
        colors=["lightgreen", "lightcoral"],
        startangle=90,
    )
    axes[2].set_title("Filter Results Summary", fontweight="bold")

    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def _portfolio_summary_metrics(
    weights: list[float],
    expected_returns: list[float],
    covariance_matrix: np.ndarray | None,
    risk_free_rate: float,
    per_asset_volatilities: list[float] | None = None,
) -> dict:
    """Honest portfolio summary (A5): Sharpe from real wᵀΣw variance.

    With a covariance matrix, portfolio volatility is sqrt(wᵀΣw). If absent
    (defensive route only), falls back to the diagonal approximation from
    per-asset volatilities with a warning — correlations then ignored.
    """
    weight_vector = np.asarray(weights, dtype=np.float64)
    return_vector = np.asarray(expected_returns, dtype=np.float64)
    portfolio_return = float(weight_vector @ return_vector)

    if covariance_matrix is not None:
        cov = np.asarray(covariance_matrix, dtype=np.float64)
        portfolio_variance = float(weight_vector @ cov @ weight_vector)
        portfolio_volatility = float(np.sqrt(max(portfolio_variance, 0.0)))
    else:
        logger.warning(
            "Portfolio summary without covariance matrix: falling back to "
            "diagonal risk approximation (correlations ignored)"
        )
        diagonal_risk = np.sqrt(sum((w * v) ** 2 for w, v in zip(weights, per_asset_volatilities or [])))
        portfolio_volatility = float(diagonal_risk)

    excess_return = portfolio_return - risk_free_log_rate(risk_free_rate)
    sharpe_ratio = (
        float("nan")
        if portfolio_volatility <= VOL_FLOOR_EPS
        else excess_return / portfolio_volatility
    )
    return {
        "return": portfolio_return,
        "volatility": portfolio_volatility,
        "sharpe": float(sharpe_ratio),
    }


def plot_optimal_portfolio_analysis(
    optimal_portfolio: dict,
    portfolio_weights: dict,
    config: PortfolioConfig,
    save_path: str | None = None,
    show_plot: bool = True,
    covariance_matrix: np.ndarray | None = None,
):
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    tickers = list(optimal_portfolio.keys())
    weights = [portfolio_weights[ticker] for ticker in tickers]
    returns = [optimal_portfolio[ticker]["annual_return"] for ticker in tickers]
    volatilities = [optimal_portfolio[ticker]["annual_volatility"] for ticker in tickers]
    sharpe_ratios = [optimal_portfolio[ticker]["sharpe_ratio"] for ticker in tickers]

    axes[0, 0].pie(weights, labels=tickers, autopct="%1.1f%%", startangle=90)
    axes[0, 0].set_title("Optimal Portfolio Weights", fontweight="bold")

    contributions = [w * r for w, r in zip(weights, returns)]
    axes[0, 1].bar(tickers, contributions, color="lightblue", alpha=0.8)
    axes[0, 1].set_title("Return Contributions by Asset", fontweight="bold")
    axes[0, 1].set_ylabel("Return Contribution")
    axes[0, 1].tick_params(axis="x", rotation=45)
    axes[0, 1].grid(True, alpha=0.3)

    scatter = axes[1, 0].scatter(
        volatilities,
        returns,
        s=[w * 1000 for w in weights],
        c=sharpe_ratios,
        cmap="RdYlGn",
        alpha=0.7,
        edgecolors="black",
    )
    for i, ticker in enumerate(tickers):
        axes[1, 0].annotate(
            ticker,
            (volatilities[i], returns[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontweight="bold",
        )

    axes[1, 0].set_title("Selected Assets: Risk-Return Profile\n(Bubble size = Weight)", fontweight="bold")
    axes[1, 0].set_xlabel("Annual Volatility")
    axes[1, 0].set_ylabel("Annual Return")
    axes[1, 0].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[1, 0], label="Sharpe Ratio")

    summary = _portfolio_summary_metrics(
        weights,
        returns,
        covariance_matrix,
        config.risk_free_rate,
        per_asset_volatilities=volatilities,
    )

    metrics_data = {
        "Portfolio Return": f"{summary['return']:.2%}",
        "Portfolio Volatility": f"{summary['volatility']:.2%}",
        "Risk-free Rate": f"{config.risk_free_rate_log:.2%} (log)",
        "Excess Return": f"{summary['return'] - config.risk_free_rate_log:.2%}",
        "Portfolio Sharpe": f"{summary['sharpe']:.2f}",
        "Number of Assets": str(len(tickers)),
        "Allocation Method": config.weight_allocation_method.replace("_", " ").title(),
    }

    axes[1, 1].axis("off")
    table_data = [[k, v] for k, v in metrics_data.items()]
    table = axes[1, 1].table(
        cellText=table_data,
        colLabels=["Metric", "Value"],
        cellLoc="left",
        loc="center",
        colWidths=[0.6, 0.4],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axes[1, 1].set_title("Portfolio Summary Statistics", fontweight="bold", pad=20)

    # This Sharpe estimate is a quick diagnostic for the summary panel, not a full
    # optimization objective or a covariance-aware portfolio performance model.
    plt.tight_layout()

    _finalize_plot(save_path, show_plot)


def print_correlation_matrix(correlation_matrix: np.ndarray, ticker_list: list):
    header = "        " + "".join(f"{ticker:<8}" for ticker in ticker_list)
    print(header)
    for i, ticker_row in enumerate(ticker_list):
        row = f"{ticker_row:<8}"
        for j, _ in enumerate(ticker_list):
            row += f"{correlation_matrix[i, j]:<8.3f}"
        print(row)


def print_covariance_matrix(covariance_matrix: np.ndarray, ticker_list: list):
    header = "        " + "".join(f"{ticker:<8}" for ticker in ticker_list)
    print(header)
    for i, ticker_row in enumerate(ticker_list):
        row = f"{ticker_row:<8}"
        for j, _ in enumerate(ticker_list):
            row += f"{covariance_matrix[i, j]:<8.6f}"
        print(row)


def print_portfolio_summary(portfolio_metrics: dict, portfolio_weights: dict):
    print("\n" + "=" * 70)
    print("OPTIMAL PORTFOLIO SUMMARY")
    print("=" * 70)
    print(f"{'Asset':<8} {'Weight':<10} {'Return':<12} {'Volatility':<12} {'Sharpe':<8}")
    print("-" * 70)

    total_weight = 0
    weighted_return = 0
    for ticker in portfolio_metrics:
        weight = portfolio_weights[ticker]
        metrics = portfolio_metrics[ticker]
        total_weight += weight
        weighted_return += weight * metrics["annual_return"]
        print(
            f"{ticker:<8} {weight:<10.2%} {metrics['annual_return']:<12.4f} "
            f"{metrics['annual_volatility']:<12.4f} {metrics['sharpe_ratio']:<8.2f}"
        )

    print("-" * 70)
    print(f"{'Total':<8} {total_weight:<10.2%} {weighted_return:<12.4f}")
    print("=" * 70)


