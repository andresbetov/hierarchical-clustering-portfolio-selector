"""B6 contract tests: leak-free walk-forward evaluation."""

import numpy as np
import pytest

from portfolio_engine.core.config import PortfolioConfig
from portfolio_engine.validation.walk_forward import (
    _iter_walk_windows,
    walk_forward_evaluate,
)


def _synthetic_bundle(n_rows=800, n_healthy=4, seed=42, flat=None):
    """Deterministic two-factor bundle with per-ticker holes."""
    rng = np.random.default_rng(seed)
    factor_a = np.exp(np.cumsum(0.0005 + rng.normal(scale=0.008, size=n_rows)))
    factor_b = np.exp(np.cumsum(0.0004 + rng.normal(scale=0.007, size=n_rows)))

    base_dates = np.datetime64("2023-01-02", "ns") + np.arange(n_rows, dtype="timedelta64[ns]")
    prices, dates = {}, {}

    for i in range(n_healthy):
        factor = factor_a if i % 2 == 0 else factor_b
        values = (
            factor
            if i == 0
            else factor * (1 + 0.002 * i) * np.exp(rng.normal(scale=0.002, size=n_rows))
        )
        ticker = f"T{i}"
        drop = {i: [10 + i, 300 - i] for i in range(n_healthy)}
        keep = np.ones(n_rows, dtype=bool)
        keep[drop[i]] = False if i > 0 else keep[drop[i]]
        if i == 1:
            keep[400:402] = False  # small hole in the middle of window 6/7
        prices[ticker] = values[keep].astype(np.float64)
        dates[ticker] = base_dates[keep]

    if flat is not None:
        prices[flat] = np.full(n_rows, 100.0).astype(np.float64)
        dates[flat] = base_dates.copy()

    return prices, dates


class TestWindowGeneration:
    def test_no_overlap_and_embargo_gap(self):
        windows = list(_iter_walk_windows(500, train_rows=120, test_rows=40, embargo_days=5))
        assert len(windows) >= 3
        for train_idx, test_idx in windows:
            gap = test_idx[0] - train_idx[-1]
            assert gap == 6  # embargo=5 means exactly 5 skipped rows between

    def test_chronological_advancement(self):
        windows = list(_iter_walk_windows(600, 100, 50, 3))
        starts = [t[0] for _, t in windows]
        assert starts == sorted(starts)

    def test_insufficient_rows_raise_named(self):
        with pytest.raises(ValueError, match="Not enough rows"):
            list(_iter_walk_windows(100, train_rows=90, test_rows=30, embargo_days=5))


class TestWalkForwardEngine:
    @pytest.fixture
    def report(self):
        prices, dates = _synthetic_bundle()
        config = PortfolioConfig(weight_allocation_method="hrp", lookback_years=2)
        return walk_forward_evaluate(
            prices,
            dates,
            config,
            train_rows=250,
            test_rows=60,
            embargo_days=5,
            risk_free_rate=0.03,
        )

    def test_multiple_folds_produced(self, report):
        assert len(report.folds) >= 3

    def test_weights_finite_and_sum_one_per_fold(self, report):
        for fold in report.folds:
            if not fold.weights:
                continue
            values = np.array(list(fold.weights.values()))
            assert np.all(np.isfinite(values))
            assert values.sum() == pytest.approx(1.0, abs=1e-9)

    def test_mutation_of_test_slice_does_not_change_fold_weights(self):
        """The ex-ante contract: OOS data cannot influence its own weights."""
        prices, dates = _synthetic_bundle()
        config = PortfolioConfig()

        normal = walk_forward_evaluate(prices, dates, config, 250, 60, 5)
        poisoned = {t: v.copy() for t, v in prices.items()}
        first_test_start = normal.folds[0].test_positions[0]
        for t in poisoned:
            poisoned[t][first_test_start:] *= 7.0  # blow up the OOS slice

        rep_poisoned = walk_forward_evaluate(poisoned, dates, config, 250, 60, 5)

        w_normal = normal.folds[0].weights
        w_poisoned = rep_poisoned.folds[0].weights
        assert w_normal.keys() == w_poisoned.keys() or set(w_normal) == set(w_poisoned)
        for k in set(w_normal) & set(w_poisoned):
            assert w_normal[k] == pytest.approx(w_poisoned[k], abs=1e-9)

    def test_first_test_day_return_included_exactly(self):
        """feat-029: the OOS series must cover every test day (test_rows
        returns), including the first day computed against the prior close."""
        n_rows = 315  # exactly one fold: 250 train + 5 embargo + 60 test
        rng = np.random.default_rng(11)
        log_returns = rng.normal(0.0, 0.01, size=n_rows)
        log_returns[255] = 0.5  # first test day: the spike under test
        log_returns[256] = 0.02  # second test day: keeps pre-fix fold valid (std > 0)
        log_returns[257:] = 0.0

        prices_path = 100.0 * np.exp(np.cumsum(log_returns))
        dates = np.datetime64("2023-01-02", "ns") + np.arange(n_rows, dtype="timedelta64[ns]")

        # Identical paths across assets: portfolio return == asset return for
        # any weights summing to 1 — the assert needs no knowledge of HRP.
        prices = {f"T{i}": prices_path.copy() for i in range(3)}
        dates_by_ticker = {f"T{i}": dates.copy() for i in range(3)}

        config = PortfolioConfig()
        report = walk_forward_evaluate(
            prices, dates_by_ticker, config, train_rows=250, test_rows=60, embargo_days=5
        )

        assert len(report.folds) == 1
        fold = report.folds[0]
        assert fold.oos_return is not None
        # 60 test returns: [0.5, 0.02, 0, ...] -> mean 0.52/60 annualized.
        assert fold.oos_return == pytest.approx(0.52 / 60 * 252, rel=1e-9)
        assert report.to_dict()["valid_folds"] == 1

    def test_aggregates_coherent_when_valid_folds_exist(self, report):
        summary = report.to_dict()
        valid = summary["valid_folds"]
        if valid == 0:
            pytest.skip("no valid folds under this synthetic configuration")
        assert summary["median_oos_volatility"] > 0
        assert 0.0 <= summary["fraction_positive_folds"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
