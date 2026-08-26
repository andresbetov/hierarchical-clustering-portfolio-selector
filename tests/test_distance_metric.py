"""M2 contract tests: signed-vs-abs distance semantics."""

import numpy as np
import pytest

from portfolio_engine.core.config import DISTANCE_METRICS, PortfolioConfig
from portfolio_engine.core.metrics import compute_correlation_distance_matrix
from portfolio_engine.portfolio.selection import (
    _resolve_distance_threshold,
    select_optimal_diversified_portfolio,
)


class TestDistanceKernel:
    def test_signed_extremes(self):
        corr = np.array([[1.0, 0.9, -0.9], [0.9, 1.0, -0.9], [-0.9, -0.9, 1.0]])
        d = compute_correlation_distance_matrix(corr, metric="signed")

        assert d[0, 1] == pytest.approx(np.sqrt(0.5 * 0.1))   # twins: tiny distance
        assert d[0, 2] == pytest.approx(np.sqrt(0.5 * 1.9))   # hedge: near max
        assert d[0, 2] > d[0, 1]

    def test_abs_mode_collapses_sign_legacy(self):
        corr = np.array([[1.0, 0.9, -0.9], [0.9, 1.0, -0.9], [-0.9, -0.9, 1.0]])
        d = compute_correlation_distance_matrix(corr, metric="abs")

        assert d[0, 1] == pytest.approx(0.1)
        assert d[0, 2] == pytest.approx(0.1)  # legacy quirk preserved on demand

    def test_unknown_metric_rejected(self):
        with pytest.raises(ValueError, match="Unknown distance metric"):
            compute_correlation_distance_matrix(np.eye(3), metric="euclidean")

    def test_nan_propagates_both_modes(self):
        corr = np.array([[1.0, np.nan], [np.nan, 1.0]])
        for mode in ("signed", "abs"):
            assert np.isnan(compute_correlation_distance_matrix(corr, metric=mode)[0, 1])


class TestThresholdConversion:
    def test_signed_conversion_preserves_semantic(self):
        # user threshold 0.65 => merge only pairs with corr > 0.65:
        t = _resolve_distance_threshold(0.65, "signed")
        d_at_065 = np.sqrt(0.5 * (1 - 0.65))
        d_at_0755 = np.sqrt(0.5 * (1 - 0.755))
        assert t == pytest.approx(d_at_065)
        # sanity: a pair with corr just above threshold is strictly inside
        assert d_at_0755 < t

    def test_abs_conversion_is_identity_style(self):
        assert _resolve_distance_threshold(0.65, "abs") == pytest.approx(0.35)

    def test_invalid_metric_raises(self):
        with pytest.raises(ValueError):
            _resolve_distance_threshold(0.65, "cosine")


class TestConfigIntegration:
    def test_default_is_signed_per_adr002(self):
        assert PortfolioConfig().distance_metric == "signed"
        assert set(DISTANCE_METRICS) == {"signed", "abs"}

    def test_invalid_metric_rejected_at_construction(self):
        with pytest.raises(ValueError, match="distance_metric"):
            PortfolioConfig(distance_metric="euclidean")


class TestClusteringContrast:
    """Behavioral pin: hedge pair merges under abs but NOT under signed."""

    def _synthetic_portfolio(self, config: PortfolioConfig):
        rng = np.random.default_rng(11)
        market = rng.normal(scale=0.01, size=(300,))
        asset_hedge = -0.8 * market + rng.normal(scale=0.004, size=(300,))
        asset_twin = 0.9 * market + rng.normal(scale=0.004, size=(300,))
        others = [rng.normal(scale=0.01, size=(300,)) for _ in range(3)]
        returns = np.column_stack([asset_hedge, asset_twin, *others])

        # Sanity: the hedge/twin pair must be strongly anti-correlated so the
        # two modes genuinely disagree about merging them.
        assert np.corrcoef(returns[:, 0], returns[:, 1])[0, 1] < -0.65

        corr = np.corrcoef(returns, rowvar=False)

        metrics = {
            f"A{i}": {
                "sharpe_ratio": 1.0,
                "annual_volatility": 0.10,  # uniform: cluster decision rides on correlations
                "annual_return": 0.10,
            }
            for i in range(returns.shape[1])
        }
        portfolio = select_optimal_diversified_portfolio(corr, metrics, config)
        return set(portfolio)

    def test_signed_keeps_hedge_and_twin_separate(self):
        config = PortfolioConfig(maximum_correlation_threshold=0.65)
        survivors = self._synthetic_portfolio(config)
        assert {"A0", "A1"} <= survivors  # both kept: they are NOT merged

    def test_abs_mode_merges_them_legacy(self):
        config = PortfolioConfig(maximum_correlation_threshold=0.65, distance_metric="abs")
        survivors = self._synthetic_portfolio(config)
        # Legacy behavior: at least one of the pair got absorbed by the cluster.
        assert not {"A0", "A1"} <= survivors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
