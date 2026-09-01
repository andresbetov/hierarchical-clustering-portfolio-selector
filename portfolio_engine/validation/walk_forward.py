"""Walk-forward out-of-sample validation (B6, De Prado CV).

For each window: fix weights on the TRAIN slice only (align → stats →
PRODUCTION FILTERS → HRP), apply them frozen on the TEST slice separated by
an embargo gap. No future information can reach the weights by construction.

Production parity (feat-035): every fold applies the same Sharpe/volatility
screens the live pipeline applies, over the train slice only — the fold's
investable universe is an ex-ante decision. Ex-ante benchmarks (equal 1/N and
inverse-volatility) face the same survivor universe on the same OOS returns,
so the engine's medians are readable against naive allocation (DeMiguel 2007;
skfolio practice).

Temporal discipline: embargo of 5 days sits inside the 5-20 day practice for
daily strategies; the implicit purge is 1 day (label horizon = daily return),
which the embargo already exceeds. Transaction costs deferred (v0.2.0).
"""

import logging
from dataclasses import dataclass, field

import numpy as np

from ..core.config import PortfolioConfig
from ..core.metrics import (
    align_prices_to_common_calendar,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
    construct_returns_matrix,
    estimate_covariance,
)
from ..portfolio.allocation import (
    _resolve_effective_bounds,
    apply_weight_constraints,
    calculate_hrp_weights,
    calculate_inverse_volatility_weights,
)
from ..portfolio.selection import apply_asset_filters

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
    # Ex-ante benchmarks over the fold's survivor universe (feat-035):
    # {"equal": {"weights": {...}, "return": ..., "volatility": ..., "sharpe": ...}, "ivp": {...}}
    benchmarks: dict[str, dict] = field(default_factory=dict)


def _median_or_none(values: list) -> float | None:
    valid = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.median(valid)) if valid else None


def _positive_fraction(values: list) -> float | None:
    valid = [v for v in values if v is not None and np.isfinite(v)]
    return float(np.mean([v > 0 for v in valid])) if valid else None


def _train_survivors(
    matrix: np.ndarray,
    train_idx: np.ndarray,
    tickers: list[str],
    config: PortfolioConfig,
    risk_free_rate: float,
) -> list[str]:
    """Production-parity screening on the TRAIN slice only (feat-035 D1).

    Reuses apply_asset_filters verbatim — same semantics and named logging
    as the live pipeline — over per-asset metrics computed from the train
    columns. Returns the surviving tickers in train order.
    """
    asset_metrics: dict = {}
    train_prices: dict = {}
    for position, ticker in enumerate(tickers):
        series = matrix[train_idx, position]
        daily = compute_logarithmic_returns(series)
        annual_return = float(calculate_annualized_return(daily, config.trading_days_per_year))
        annual_volatility = float(calculate_annualized_volatility(daily, config.trading_days_per_year))
        asset_metrics[ticker] = {
            "daily_returns": daily,
            "annual_return": annual_return,
            "annual_volatility": annual_volatility,
            "sharpe_ratio": calculate_sharpe_ratio(annual_return, annual_volatility, risk_free_rate),
        }
        train_prices[ticker] = series

    filtered_metrics, _ = apply_asset_filters(
        asset_metrics,
        train_prices,
        config.minimum_sharpe_threshold,
        config.maximum_volatility_threshold,
    )
    return list(filtered_metrics.keys())


def _oos_metrics(daily_returns: np.ndarray, risk_free_rate: float, trading_days: int) -> dict | None:
    """Annualized return/volatility/Sharpe over an OOS return series (D5).

    NaN-blind guard (adversarial review feat-035): a single return makes
    std(ddof=1) NaN, and `NaN <= 0` is False — the negated comparison
    catches it, so degenerate folds are excluded instead of reported as
    valid-with-NaN metrics.
    """
    if len(daily_returns) < 2 or not (float(np.std(daily_returns, ddof=1)) > 0):
        return None
    realized_return = float(np.mean(daily_returns) * trading_days)
    realized_vol = float(np.std(daily_returns, ddof=1) * np.sqrt(trading_days))
    return {
        "return": realized_return,
        "volatility": realized_vol,
        "sharpe": (realized_return - risk_free_rate) / realized_vol,
    }


def _benchmark_median(folds: list, name: str, key: str) -> float | None:
    values = []
    for fold in folds:
        entry = fold.benchmarks.get(name)
        values.append(entry.get(key) if entry else None)
    return _median_or_none(values)


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
            "median_oos_return_equal": _benchmark_median(self.folds, "equal", "return"),
            "median_oos_volatility_equal": _benchmark_median(self.folds, "equal", "volatility"),
            "median_oos_sharpe_equal": _benchmark_median(self.folds, "equal", "sharpe"),
            "median_oos_return_ivp": _benchmark_median(self.folds, "ivp", "return"),
            "median_oos_volatility_ivp": _benchmark_median(self.folds, "ivp", "volatility"),
            "median_oos_sharpe_ivp": _benchmark_median(self.folds, "ivp", "sharpe"),
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

    Per fold: align → train metrics → PRODUCTION FILTERS (ex-ante universe)
    → HRP on survivors; freeze weights; score OOS returns on TEST with those
    weights, alongside ex-ante equal/ivp benchmarks over the same survivor
    universe and the same OOS returns. Folds whose train filters leave no
    survivors or whose OOS slice produces degenerate risk are marked invalid
    and excluded from aggregates (engine and benchmarks alike).
    """
    rf = config.risk_free_rate if risk_free_rate is None else risk_free_rate
    report = WalkForwardReport()

    aligned = align_prices_to_common_calendar(prices_by_ticker, dates_by_ticker)
    tickers = list(aligned.keys())
    matrix = np.column_stack([aligned[ticker] for ticker in tickers])
    n_rows = matrix.shape[0]

    for fold_index, (train_idx, test_idx) in enumerate(_iter_walk_windows(n_rows, train_rows, test_rows, embargo_days)):
        relaxed = False
        try:
            # Production parity (feat-035 D1): the fold's investable universe
            # is decided by the SAME screens the live pipeline applies, on
            # TRAIN data only — an ex-ante decision, never test-informed.
            survivors = _train_survivors(matrix, train_idx, tickers, config, rf)
            if not survivors:
                raise ValueError("no assets survive the train filters in this fold")

            position_of = {t: i for i, t in enumerate(tickers)}
            daily_train = construct_returns_matrix({
                t: matrix[train_idx, position_of[t]] for t in survivors
            })
            cov_train = estimate_covariance(daily_train, config.covariance_estimator)

            raw_weights = calculate_hrp_weights(cov_train, linkage_method=config.linkage_method)
            min_bound, max_bound = _resolve_effective_bounds(len(survivors), config)
            if max_bound != config.maximum_single_asset_weight or min_bound != config.minimum_single_asset_weight:
                relaxed = True
            constrained = apply_weight_constraints(raw_weights, min_bound, max_bound)

            # Embed survivor weights into the full-ticker vector (feat-035
            # D2): excluded tickers get exactly 0, keeping log_test columns
            # aligned without slicing the extended test window.
            def _embed(survivor_weights: np.ndarray) -> np.ndarray:
                by_ticker = dict(zip(survivors, survivor_weights))
                return np.array([by_ticker.get(t, 0.0) for t in tickers])

            weight_vector = _embed(constrained)

            # OOS returns cover EVERY test day (exactly test_rows values): the
            # first test-day return is log(P[test_start]/P[test_start-1]), using
            # the last price before the window (embargo row, or last train row
            # when embargo_days=0) — past information, no leakage (feat-029).
            extended_test = matrix[np.concatenate(([test_idx[0] - 1], test_idx))]
            log_test = np.log(extended_test[1:] / extended_test[:-1])
            portfolio_daily_returns = log_test @ weight_vector

            engine_metrics = _oos_metrics(portfolio_daily_returns, rf, config.trading_days_per_year)
            if engine_metrics is None:
                raise FloatingPointError("degenerate OOS risk")

            # Ex-ante benchmarks (feat-035 D3/D5): weights fixed exclusively
            # with train information (survivor count for equal; train vols
            # for ivp), scored frozen on the SAME OOS return series.
            n_survivors = len(survivors)
            equal_weights = np.full(n_survivors, 1.0 / n_survivors)
            train_vols = np.std(daily_train, axis=0, ddof=1) * np.sqrt(config.trading_days_per_year)
            ivp_weights = calculate_inverse_volatility_weights(train_vols)

            benchmarks: dict[str, dict] = {}
            for name, survivor_weights in (("equal", equal_weights), ("ivp", ivp_weights)):
                bench_metrics = _oos_metrics(log_test @ _embed(survivor_weights), rf, config.trading_days_per_year)
                benchmarks[name] = {
                    "weights": {t: float(w) for t, w in zip(survivors, survivor_weights)},
                    **(bench_metrics or {"return": None, "volatility": None, "sharpe": None}),
                }

            fold = WalkForwardFold(
                index=fold_index,
                train_positions=(int(train_idx[0]), int(train_idx[-1]) + 1),
                test_positions=(int(test_idx[0]), int(test_idx[-1]) + 1),
                tickers=list(tickers),
                weights={t: float(w) for t, w in zip(survivors, constrained)},
                oos_return=engine_metrics["return"],
                oos_volatility=engine_metrics["volatility"],
                oos_sharpe=engine_metrics["sharpe"],
                mandate_relaxed=relaxed,
                benchmarks=benchmarks,
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
