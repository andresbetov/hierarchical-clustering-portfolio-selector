"""C3 numeric-correctness contract tests at selection/allocation boundaries."""

import logging

import numpy as np
import pytest

from portfolio_engine.portfolio.allocation import (
    calculate_inverse_volatility_weights,
    calculate_risk_parity_weights,
)
from portfolio_engine.portfolio.selection import apply_asset_filters


@pytest.fixture(autouse=True)
def _restore_package_propagation():
    """Keep caplog working regardless of test-session ordering.

    Other contract tests may call configure_logging(), which sets
    propagate=False on the package root logger — that would hide these
    records from the root-attached capture handler.
    """
    pkg_logger = logging.getLogger("portfolio_engine")
    original = pkg_logger.propagate
    pkg_logger.propagate = True
    yield
    pkg_logger.propagate = original


def _metrics(ticker_sharpe=1.0, ticker_vol=0.15):
    return {"sharpe_ratio": ticker_sharpe, "annual_volatility": ticker_vol}


class TestFilterExcludesNonFiniteNamed:
    def test_nan_inf_sharpe_excluded_and_named(self, caplog):
        metrics = {
            "GOOD": _metrics(),
            "BAD1": {"sharpe_ratio": float("nan"), "annual_volatility": 0.2},
            "BAD2": {"sharpe_ratio": float("inf"), "annual_volatility": 0.2},
        }
        prices = {t: np.array([100.0, 101.0]) for t in metrics}

        with caplog.at_level(logging.WARNING):
            filtered, _ = apply_asset_filters(metrics, prices, minimum_sharpe=0.5, maximum_volatility=0.25)

        assert set(filtered) == {"GOOD"}
        flat_messages = " ".join(caplog.messages)
        assert "BAD1" in flat_messages and "non_finite" in flat_messages
        assert "BAD2" in flat_messages

    def test_non_finite_volatility_excluded_and_named(self, caplog):
        metrics = {
            "OK": _metrics(),
            "FLAT": {"sharpe_ratio": float("nan"), "annual_volatility": float("nan")},
        }
        prices = {t: np.array([100.0, 101.0]) for t in metrics}

        with caplog.at_level(logging.WARNING):
            filtered, _ = apply_asset_filters(metrics, prices, minimum_sharpe=0.5)

        assert set(filtered) == {"OK"}
        assert any("FLAT" in m for m in caplog.messages)

    def test_threshold_rejections_also_named(self, caplog):
        metrics = {"LOW": _metrics(ticker_sharpe=0.1), "FINE": _metrics()}
        prices = {t: np.array([100.0, 101.0]) for t in metrics}

        with caplog.at_level(logging.WARNING):
            filtered, _ = apply_asset_filters(metrics, prices, minimum_sharpe=0.5)

        assert set(filtered) == {"FINE"}
        flat_messages = " ".join(caplog.messages)
        assert "LOW" in flat_messages and "below_min_sharpe" in flat_messages


class TestRiskParityGuards:
    def test_singular_covariance_returns_finite_normalized_weights(self):
        col = np.linspace(-0.01, 0.01, 50)
        cov = np.cov(np.column_stack([col, col]), rowvar=False)
        weights = calculate_risk_parity_weights(cov)

        assert np.all(np.isfinite(weights))
        assert weights.sum() == pytest.approx(1.0, abs=1e-9)
        assert (weights > 0).all()

    def test_degenerate_zero_variance_flags_warning(self, caplog):
        cov = np.zeros((2, 2))
        with caplog.at_level(logging.WARNING):
            weights = calculate_risk_parity_weights(cov)

        assert np.all(np.isfinite(weights))
        assert any("degenerate portfolio variance" in m for m in caplog.messages)

    def test_exhausted_iterations_warns_but_returns_usable(self, caplog):
        rng = np.random.default_rng(42)
        noise = rng.normal(size=(60, 3)) * 0.01
        cov = np.cov(noise, rowvar=False) + np.eye(3) * 1e-6

        with caplog.at_level(logging.WARNING):
            weights = calculate_risk_parity_weights(cov, max_iterations=1, tolerance=1e-20)

        assert np.all(np.isfinite(weights))
        assert weights.sum() == pytest.approx(1.0, abs=1e-9)
        assert any("did not converge" in m for m in caplog.messages)

    def test_healthy_covariance_converges_to_equal_risk(self):
        rng = np.random.default_rng(7)
        returns = rng.normal(scale=0.01, size=(250, 4))
        cov = np.cov(returns, rowvar=False)

        weights = calculate_risk_parity_weights(cov)
        marginal = cov @ weights
        contributions = weights * marginal / float(weights @ marginal)

        assert np.allclose(contributions, 0.25, atol=1e-6)  # equalized risk
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)


class TestInverseVolGuard:
    def test_zero_volatility_yields_finite_positive_normalized_weights(self):
        weights = calculate_inverse_volatility_weights(np.array([0.0, 0.2]))

        assert np.all(np.isfinite(weights))
        assert (weights > 0).all()
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
