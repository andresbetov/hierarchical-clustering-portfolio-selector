"""Console entrypoint for the standard portfolio analysis run.

Deliberately argument-free: CLI flags (--config/--universe) are deferred to
Phase 4 alongside config files. Replicates exactly what
scripts/assets-investment.py did, now from an installable location.
"""

import logging

from .app.pipeline import generate_complete_analysis_report
from .core.config import PortfolioConfig
from .core.logging_utils import configure_logging
from .viz.reporting import print_portfolio_summary

logger = logging.getLogger(__name__)

DEFAULT_UNIVERSE: list[str] = [
    "JNJ",   # Johnson & Johnson
    "JPM",   # JPMorgan Chase & Co.
    "V",     # Visa
    "PG",    # Procter & Gamble
    "HD",    # The Home Depot
    "MA",    # Mastercard
    "CVX",   # Chevron
    "PFE",   # Pfizer
    "ABBV",  # AbbVie
    "TMO",   # Thermo Fisher Scientific
    "MRK",   # Merck & Co.
    "WMT",   # Walmart
]


def main() -> None:
    """Run the standard offline-configured analysis and print the summary."""
    configure_logging()

    portfolio_config = PortfolioConfig()

    logger.warning(
        "Universe restricted to Yahoo Finance tickers: tickers=%d",
        len(DEFAULT_UNIVERSE),
    )

    (
        all_metrics,
        filtered_metrics,
        optimal_portfolio,
        portfolio_weights,
    ) = generate_complete_analysis_report(
        DEFAULT_UNIVERSE,
        portfolio_config,
        save_plots=True,
        show_plots=False,
    )

    print_portfolio_summary(optimal_portfolio, portfolio_weights)


if __name__ == "__main__":
    main()
