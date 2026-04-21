from pathlib import Path
import sys

# Make project root importable when running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from portfolio_engine import (
    PortfolioConfig,
    configure_logging,
    generate_complete_analysis_report,
    print_portfolio_summary,
)


if __name__ == "__main__":
    configure_logging()

    portfolio_config = PortfolioConfig()

    stock_symbols = [
        "JNJ",
        "JPM",
        "V",
        "PG",
        "HD",
        "MA",
        "CVX",
        "PFE",
        "ABBV",
        "TMO",
        "MRK",
        "WMT",
    ]

    all_metrics, filtered_metrics, optimal_portfolio, portfolio_weights = generate_complete_analysis_report(
        stock_symbols,
        portfolio_config,
        save_plots=True,
        show_plots=False,
    )

    print_portfolio_summary(optimal_portfolio, portfolio_weights)