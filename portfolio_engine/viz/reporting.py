"""Visualization and text-report utilities for portfolio outputs."""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from ..core.config import PortfolioConfig


def _finalize_plot(save_path: str = None, show_plot: bool = True):
    """Apply consistent save/show behavior for every chart.

    Uses non-blocking display so batch report generation does not stop between
    figures when `show_plot=True`.
    """

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    if show_plot:
        # Non-blocking per figure; caller can block once at the end if desired.
        plt.show(block=False)
        plt.pause(0.001)
    else:
        plt.close()


def plot_historical_prices(historical_prices: dict, price_dates: dict, save_path: str = None, show_plot: bool = True):
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
    save_path: str = None,
    show_plot: bool = True,
):
    plt.figure(figsize=(12, 8))

    returns = [metrics["annual_return"] for metrics in asset_metrics.values()]
    volatilities = [metrics["annual_volatility"] for metrics in asset_metrics.values()]
    sharpe_ratios = [metrics["sharpe_ratio"] for metrics in asset_metrics.values()]
    tickers = list(asset_metrics.keys())

    scatter = plt.scatter(volatilities, returns, c=sharpe_ratios, s=100, cmap="RdYlGn", alpha=0.7, edgecolors="black")

    for i, ticker in enumerate(tickers):
        plt.annotate(ticker, (volatilities[i], returns[i]), xytext=(5, 5), textcoords="offset points", fontweight="bold")

    plt.axhline(y=config.risk_free_rate, color="blue", linestyle="--", label=f"Risk-free rate ({config.risk_free_rate:.1%})")
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
    save_path: str = None,
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
    save_path: str = None,
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


def plot_asset_metrics_comparison(asset_metrics: dict, save_path: str = None, show_plot: bool = True):
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
        axes[1, 1].annotate(ticker, (volatilities[i], returns[i]), xytext=(3, 3), textcoords="offset points", fontsize=8)
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
    save_path: str = None,
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


def plot_optimal_portfolio_analysis(
    optimal_portfolio: dict,
    portfolio_weights: dict,
    config: PortfolioConfig,
    save_path: str = None,
    show_plot: bool = True,
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
        axes[1, 0].annotate(ticker, (volatilities[i], returns[i]), xytext=(5, 5), textcoords="offset points", fontweight="bold")

    axes[1, 0].set_title("Selected Assets: Risk-Return Profile\n(Bubble size = Weight)", fontweight="bold")
    axes[1, 0].set_xlabel("Annual Volatility")
    axes[1, 0].set_ylabel("Annual Return")
    axes[1, 0].grid(True, alpha=0.3)
    plt.colorbar(scatter, ax=axes[1, 0], label="Sharpe Ratio")

    portfolio_return = sum(w * r for w, r in zip(weights, returns))
    portfolio_sharpe = portfolio_return / np.sqrt(sum((w * v) ** 2 for w, v in zip(weights, volatilities)))

    metrics_data = {
        "Portfolio Return": f"{portfolio_return:.2%}",
        "Risk-free Rate": f"{config.risk_free_rate:.2%}",
        "Excess Return": f"{portfolio_return - config.risk_free_rate:.2%}",
        "Portfolio Sharpe": f"{portfolio_sharpe:.2f}",
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


