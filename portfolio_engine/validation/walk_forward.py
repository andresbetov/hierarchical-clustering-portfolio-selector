"""Walk-forward out-of-sample validation (B6, De Prado CV).

For each window: fix weights on the TRAIN slice only (align → stats → HRP),
apply them frozen on the TEST slice separated by an embargo gap. No future
information can reach the weights by construction.

First iteration scope: buy-and-hold within window, transaction costs deferred.
"""

import logging
from dataclasses import dataclass, field

import numpy as np

from ..core.config import PortfolioConfig
from ..core.metrics import (
    align_prices_to_common_calendar,
    calculate_covariance_matrix,
    construct_returns_matrix,
)
from ..portfolio.allocation import _resolve_effective_bounds, apply_weight_constraints, calculate_hrp_weights

logger = logging.getLogger(__name__)


def _iter_walk_windows(
    n_rows: int,
    train_rows: int,
    test_rows: int,
    embargo_days: int = 0,
):
    """Yield (train_slice, test_slice) index pairs without temporal leakage.

    Layout per fold: [train ... | embargo | test]. Raises ValueError when the
    parameters cannot produce a single complete window.
    """
    if train_rows < 2 or test_rows < 1:
        raise ValueError(f"train_rows>=2 and test_rows>=1 required (got {train_rows}/{test_rows})")
    if embargo_days < 0:
        raise ValueError(f"embargo_days must be >= 0, got {embargo_days}")

    span_needed = train_rows + embargo_days + test_rows
    if n_rows < span_needed:
        raise ValueError(
            f"Not enough rows: n={n_rows} < train({train_rows}) + embargo({embargo_days}) "
            f"+ test({test_rows}) = {span_needed}"
        )

    start = 0
    while True:
        train_end = start + train_rows
        test_start = train_end + embargo_days
        test_end = test_start + test_rows

        if test_end > n_rows:
            break

        yield np.arange(start, train_end), np.arange(test_start, test_end)
        start += test_rows


@dataclass
class WalkForwardFold:
    index: int
    train_positions: tuple[int, int]  # inclusive/exclusive
    test_positions: tuple[int, int]
    tickers: list[str]
    weights: dict[str, float]
    oos_return: float | None
    oos_volatility: float | None
    oos_sharpe: float | None
    mandate_relaxed: bool


def _median_or_none(values: list) -> float | None:
    valid = [v for v in values if v is not None]
    return float(np.median(valid)) if valid else None


def _positive_fraction(values: list) -> float | None:
    valid = [v for v in values if v is not None]
    return float(np.mean([v > 0 for v in valid])) if valid else None


@dataclass
class WalkForwardReport:
    folds: list[WalkForwardFold] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "n_folds": len(self.folds),
            "valid_folds": sum(1 for f in self.folds if f.oos_sharpe is not None),
            "median_oos_return": _median_or_none([f.oos_return for f in self.folds]),
            "median_oos_volatility": _median_or_none([f.oos_volatility for f in self.folds]),
            "median_oos_sharpe": _median_or_none([f.oos_sharpe for f in self.folds]),
            "fraction_positive_folds": _positive_fraction(
                [f.oos_return for f in self.folds]
            ),
            "relaxed_folds": sum(1 for f in self.folds if f.mandate_relaxed),
        }


def walk_forward_evaluate(
    prices_by_ticker: dict[str, np.ndarray],
    dates_by_ticker: dict[str, np.ndarray],
    config: PortfolioConfig,
    train_rows: int = 250,
    test_rows: int = 60,
    embargo_days: int = 5,
    risk_free_rate: float | None = None,
) -> WalkForwardReport:
    """Run deterministic walk-forward evaluation over aligned price series.

    Per fold: align → stats → HRP on TRAIN; freeze weights; score OOS returns
    on TEST with those weights. Folds whose OOS slice produces degenerate risk
    are marked invalid and excluded from aggregates.
    """
    from datetime import timedelta  # noqa: F401 — reserved for date-based reporting

    rf = config.risk_free_rate if risk_free_rate is None else risk_free_rate
    report = WalkForwardReport()

    aligned = align_prices_to_common_calendar(prices_by_ticker, dates_by_ticker)
    tickers = list(aligned.keys())
    matrix = np.column_stack([aligned[ticker] for ticker in tickers])
    n_rows = matrix.shape[0]

    for fold_index, (train_idx, test_idx) in enumerate(_iter_walk_windows(n_rows, train_rows, test_rows, embargo_days)):
        relaxed = False
        try:
            daily_train = construct_returns_matrix({
                t: matrix[train_idx, i] for i, t in enumerate(tickers)
            })
            cov_train = calculate_covariance_matrix(daily_train)

            raw_weights = calculate_hrp_weights(cov_train)
            min_bound, max_bound = _resolve_effective_bounds(len(tickers), config)
            if max_bound != config.maximum_single_asset_weight or min_bound != config.minimum_single_asset_weight:
                relaxed = True
            constrained = apply_weight_constraints(raw_weights, min_bound, max_bound)

            weight_vector = np.array([constrained[i] for i in range(len(tickers))])

            # OOS returns cover EVERY test day (exactly test_rows values): the
            # first test-day return is log(P[test_start]/P[test_start-1]), using
            # the last price before the window (embargo row, or last train row
            # when embargo_days=0) — past information, no leakage (feat-029).
            extended_test = matrix[np.concatenate(([test_idx[0] - 1], test_idx))]
            log_test = np.log(extended_test[1:] / extended_test[:-1])
            portfolio_daily_returns = log_test @ weight_vector

            if len(portfolio_daily_returns) == 0 or float(np.std(portfolio_daily_returns, ddof=1)) <= 0:
                raise FloatingPointError("degenerate OOS risk")

            realized_return = float(np.mean(portfolio_daily_returns) * config.trading_days_per_year)
            realized_vol = float(np.std(portfolio_daily_returns, ddof=1) * np.sqrt(config.trading_days_per_year))
            sharpe = (realized_return - rf) / realized_vol

            fold = WalkForwardFold(
                index=fold_index,
                train_positions=(int(train_idx[0]), int(train_idx[-1]) + 1),
                test_positions=(int(test_idx[0]), int(test_idx[-1]) + 1),
                tickers=list(tickers),
                weights={t: float(w) for t, w in zip(tickers, weight_vector)},
                oos_return=realized_return,
                oos_volatility=realized_vol,
                oos_sharpe=sharpe,
                mandate_relaxed=relaxed,
            )
        except (FloatingPointError, ValueError) as exc:
            logger.warning("Walk-forward fold %d invalid: reason=%s", fold_index, exc)
            fold = WalkForwardFold(
                index=fold_index,
                train_positions=(int(train_idx[0]), int(train_idx[-1]) + 1),
                test_positions=(int(test_idx[0]), int(test_idx[-1]) + 1),
                tickers=list(tickers),
                weights={},
                oos_return=None,
                oos_volatility=None,
                oos_sharpe=None,
                mandate_relaxed=relaxed,
            )

        report.folds.append(fold)

    valid = [f for f in report.folds if f.oos_sharpe is not None]
    logger.info(
        "Walk-forward complete: folds=%d valid=%d median_oos_sharpe=%.3f",
        len(report.folds), len(valid), report.to_dict()["median_oos_sharpe"] or float("nan"),
    )
    return report
