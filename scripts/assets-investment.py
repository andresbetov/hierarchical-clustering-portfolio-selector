import sys
from pathlib import Path

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

    # Warning: This project only supports tickers listed on Yahoo Finance.
    stock_symbols = [
        "JNJ",  # Johnson & Johnson
        "JPM",  # JPMorgan Chase & Co.
        "V",  # Visa
        "PG",  # Procter & Gamble
        "HD",  # The Home Depot
        "MA",  # Mastercard
        "CVX",  # Chevron
        "PFE",  # Pfizer
        "ABBV",  # AbbVie
        "TMO",  # Thermo Fisher Scientific
        "MRK",  # Merck & Co.
        "WMT",  # Walmart
    ]

    all_metrics, filtered_metrics, optimal_portfolio, portfolio_weights = generate_complete_analysis_report(
        stock_symbols,
        portfolio_config,
        save_plots=True,
        show_plots=False,
    )

    print_portfolio_summary(optimal_portfolio, portfolio_weights)
