"""A5 contract tests: reported portfolio Sharpe uses real covariance risk."""

import logging

import numpy as np
import pytest

from portfolio_engine.viz.reporting import _portfolio_summary_metrics


def _two_asset_cov(rho: float) -> np.ndarray:
    """Correlation-with-rho covariance for equal vols 0.15/0.15."""
    var = 0.15**2
    return np.array([[var, rho * var], [rho * var, var]])


WEIGHTS = [0.5, 0.5]
RETURNS = [0.10, 0.08]
RF = 0.03


class TestSummaryMetrics:
    def test_diagonal_cov_matches_legacy_formula(self):
        """ρ=0 must reproduce the old sqrt(sum((w·v)^2)) result exactly."""
        cov = _two_asset_cov(0.0)
        summary = _portfolio_summary_metrics(WEIGHTS, RETURNS, cov, RF)

        legacy_vol = np.sqrt((0.5 * 0.15) ** 2 + (0.5 * 0.15) ** 2)
        assert summary["volatility"] == pytest.approx(float(legacy_vol), rel=1e-12)
        assert summary["sharpe"] == pytest.approx(
            (summary["return"] - RF) / legacy_vol, rel=1e-12
        )

    def test_high_correlation_increases_risk_decreases_sharpe(self):
        rho_zero = _portfolio_summary_metrics(WEIGHTS, RETURNS, _two_asset_cov(0.0), RF)
        rho_nine = _portfolio_summary_metrics(WEIGHTS, RETURNS, _two_asset_cov(0.9), RF)

        assert rho_nine["volatility"] > rho_zero["volatility"]
        assert rho_nine["sharpe"] < rho_zero["sharpe"]

    def test_perfect_correlation_bounded_by_weighted_average_vol(self):
        """With ρ=1 and equal vols: portfolio vol == weighted average vol exactly."""
        perfect = _portfolio_summary_metrics(WEIGHTS, RETURNS, _two_asset_cov(1.0), RF)
        assert perfect["volatility"] == pytest.approx(0.15, rel=1e-12)

    def test_manual_wtw_agreement_two_assets(self):
        cov = np.array([[0.04, 0.006], [0.006, 0.01]])
        weights = [0.7, 0.3]
        summary = _portfolio_summary_metrics(weights, [0.12, 0.07], cov, 0.02)

        manual_variance = float(np.asarray(weights) @ cov @ np.asarray(weights))
        assert summary["volatility"] == pytest.approx(np.sqrt(manual_variance), rel=1e-12)

    def test_missing_cov_falls_back_with_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            summary = _portfolio_summary_metrics(
                WEIGHTS,
                RETURNS,
                None,
                RF,
                per_asset_volatilities=[0.15, 0.15],
            )

        flat_messages = " ".join(caplog.messages)
        assert "diagonal risk approximation" in flat_messages
        assert summary["volatility"] is not None

    def test_nan_sharpe_for_degenerate_risk(self):
        zero_weights = [0.0, 0.0]
        # Zero-weight vector on a positive-definite cov produces vol=0:
        summary = _portfolio_summary_metrics(
            zero_weights, RETURNS, _two_asset_cov(0.0), RF
        )
        assert summary["volatility"] == 0.0
        assert np.isnan(summary["sharpe"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
