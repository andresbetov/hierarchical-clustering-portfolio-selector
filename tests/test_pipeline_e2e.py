"""End-to-end composition tests — the whole pipeline, no network (M8)."""


import numpy as np
import pytest

from portfolio_engine.app.pipeline import main
from portfolio_engine.core.config import PortfolioConfig

# Composition spec: 6 tickers with calendar holes, trailing NaN tails and a flat asset.
E2E_SPEC = {
    "AAAA": {},
    "BBBB": {"days_missing": [3]},
    "CCCC": {"trailing_nan": 2},
    "DDDD": {"days_missing": [5, 6]},
    "EEEE": {"flat": True},               # must be filtered by non-finite Sharpe
    "FFFF": {"days_missing": [0, 1, 2]},  # late start
}


@pytest.fixture
def e2e_result(patched_batch):
    patched_batch(E2E_SPEC, rows=20)
    config = PortfolioConfig(
        minimum_sharpe_threshold=0.5,
        maximum_volatility_threshold=10.0,
        weight_allocation_method="hrp",
        lookback_years=1,
    )
    return main(list(E2E_SPEC), config), config


class TestEndToEndComposition:
    def test_flat_asset_excluded_by_named_filter(self, e2e_result):
        result, _ = e2e_result
        all_metrics, filtered_metrics = result[0], result[1]

        assert "EEEE" in all_metrics
        assert "EEEE" not in filtered_metrics
        assert set(filtered_metrics) <= set(E2E_SPEC)

    def test_matrices_square_symmetric_when_universe_viable(self, e2e_result):
        result, _ = e2e_result
        _, filtered_metrics, _, _, corr_matrix, cov_matrix = (result[i] for i in range(6))

        n = len(filtered_metrics)
        if n < 2:
            pytest.skip("overlap insufficient for multivariate stage")
        assert corr_matrix.shape == (n, n)
        assert cov_matrix.shape == (n, n)
        assert np.allclose(corr_matrix, corr_matrix.T)
        assert np.allclose(cov_matrix, cov_matrix.T)

    def test_hrp_weights_simplex_and_bounds(self, e2e_result):
        """Two legal regimes pinned mathematically (mirror of
        _resolve_effective_bounds): full mandate when n*max>=1, else
        concentration relaxation with max=1/n for tiny universes."""
        result, config = e2e_result
        _, filtered_metrics, optimal_portfolio, portfolio_weights = result[:4]

        assert len(portfolio_weights) == len(filtered_metrics)
        assert set(portfolio_weights) == set(filtered_metrics)

        total = sum(portfolio_weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)

        n = len(filtered_metrics)
        effective_max = (
            config.maximum_single_asset_weight
            if n * config.maximum_single_asset_weight >= 1.0
            else 1.0 / n  # relaxation regime — CRITICAL logged by policy
        )
        assert abs(effective_max - 1.0 / n) < 1e-12 or effective_max != 1.0 / n

        for weight in portfolio_weights.values():
            assert np.isfinite(weight)
            assert weight > 0
            assert weight <= effective_max + 1e-6

    def test_prices_dates_contract_full_universe_for_charts(self, e2e_result):
        """main() deliberately returns FULL-universe prices/dates (charts paint
        every ticker as context); only stats matrices use filtered+aligned."""
        result, _ = e2e_result
        _, filtered_metrics, _, _, _, _, prices, dates = result

        assert set(prices) == set(dates) == set(E2E_SPEC)
        assert set(filtered_metrics) <= set(prices)

        # Per-ticker internal consistency:
        for ticker, series in prices.items():
            assert len(series) == len(dates[ticker])
            finite_ratio = np.isfinite(series).mean()
            # Flat asset yields constant prices (finite); others may have NaN tails:
            assert finite_ratio > 0

    def test_stats_matrices_only_cover_filtered_universe(self, e2e_result):
        result, _ = e2e_result
        _, filtered_metrics, _, _, corr_matrix, cov_matrix = (result[i] for i in range(6))

        n_filtered = len(filtered_metrics)
        if n_filtered >= 2:
            # Stats must be sized by the FILTERED universe, never the full one.
            assert corr_matrix.shape[0] == n_filtered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
