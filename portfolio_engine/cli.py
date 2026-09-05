"""Console entrypoint for the standard portfolio analysis run."""

import argparse
import logging
from pathlib import Path

from .app.pipeline import generate_complete_analysis_report
from .core.config import (
    COVARIANCE_ESTIMATORS,
    LINKAGE_METHODS,
    WEIGHT_ALLOCATION_METHODS,
    PortfolioConfig,
)
from .core.logging_utils import configure_logging
from .data.provider import YFinanceProvider
from .data.universe import DEFAULT_UNIVERSE_PATH, load_universe
from .viz.reporting import print_portfolio_summary

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hierarchical clustering portfolio selector")
    parser.add_argument(
        "--universe",
        type=str,
        default=str(DEFAULT_UNIVERSE_PATH),
        metavar="PATH",
        help="Path to YAML universe file (default: config/universe.yaml)",
    )
    parser.add_argument(
        "--method",
        dest="weight_allocation_method",
        choices=WEIGHT_ALLOCATION_METHODS,
        default="hrp",
        help="Weight allocation method %(choices)s (default: %(default)s)",
    )
    parser.add_argument(
        "--covariance-estimator",
        dest="covariance_estimator",
        choices=COVARIANCE_ESTIMATORS,
        default="sample",
        help="Covariance estimator %(choices)s (default: %(default)s)",
    )
    parser.add_argument(
        "--linkage",
        "--linkage-method",
        dest="linkage_method",
        choices=LINKAGE_METHODS,
        default="single",
        help="HRP linkage method %(choices)s (default: %(default)s)",
    )
    parser.add_argument(
        "--save",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save plots to disk (use --no-save to skip)",
    )
    parser.add_argument(
        "--show",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Display plots interactively (use --no-show to hide, default: hidden)",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        default=False,
        help="Ignore parquet cache and force re-download",
    )
    return parser


def main(argv: list[str] | None = None, universe_path: str | None = None) -> None:
    """Run the standard configured analysis over the YAML universe.

    `universe_path` explicit param is legacy; prefer --universe flag.
    `argv` allows test injection without sys.argv side-effect.
    """
    if universe_path is not None:
        if argv is not None:
            logger.warning("universe_path overrides --universe/argv flags: argv=%s ignored", argv)
        resolved_universe = universe_path
        refresh = False
        # Legacy path preserves defaults for method/cov/linkage and save/show
        portfolio_config = PortfolioConfig()
        save_plots = True
        show_plots = False
    else:
        args = _build_parser().parse_args(argv)
        resolved_universe = args.universe
        refresh = bool(args.refresh_cache)
        portfolio_config = PortfolioConfig(
            weight_allocation_method=args.weight_allocation_method,
            covariance_estimator=args.covariance_estimator,
            linkage_method=args.linkage_method,
        )
        save_plots = bool(args.save)
        show_plots = bool(args.show)

    configure_logging()

    universe = load_universe(resolved_universe)

    logger.warning(
        "Universe restricted to Yahoo Finance tickers: tickers=%d",
        len(universe),
    )

    provider = YFinanceProvider(
        cache_dir=Path("data/cache"),
        refresh_cache=refresh,
    )

    (
        all_metrics,
        filtered_metrics,
        optimal_portfolio,
        portfolio_weights,
    ) = generate_complete_analysis_report(
        universe,
        portfolio_config,
        save_plots=save_plots,
        show_plots=show_plots,
        provider=provider,
    )

    print_portfolio_summary(optimal_portfolio, portfolio_weights)


if __name__ == "__main__":
    main()
