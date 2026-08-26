"""Console entrypoint for the standard portfolio analysis run.

CLI flags beyond --universe remain deferred to Phase 4; the universe itself
is externalized to config/universe.yaml (B2) and loaded at runtime.
"""

import logging

from .app.pipeline import generate_complete_analysis_report
from .core.config import PortfolioConfig
from .core.logging_utils import configure_logging
from .data.universe import DEFAULT_UNIVERSE_PATH, load_universe
from .viz.reporting import print_portfolio_summary

logger = logging.getLogger(__name__)


def main(universe_path: str | None = None) -> None:
    """Run the standard configured analysis over the YAML universe.

    `universe_path` defaults to config/universe.yaml (B2 externalization).
    """
    configure_logging()

    portfolio_config = PortfolioConfig()
    universe = load_universe(universe_path or DEFAULT_UNIVERSE_PATH)

    logger.warning(
        "Universe restricted to Yahoo Finance tickers: tickers=%d",
        len(universe),
    )

    (
        all_metrics,
        filtered_metrics,
        optimal_portfolio,
        portfolio_weights,
    ) = generate_complete_analysis_report(
        universe,
        portfolio_config,
        save_plots=True,
        show_plots=False,
    )

    print_portfolio_summary(optimal_portfolio, portfolio_weights)


if __name__ == "__main__":
    main()
