"""B5 contract tests: quadratic solvers without explicit inversion."""

import logging

import numpy as np
import pytest

from portfolio_engine.portfolio.allocation import (
    _ensure_positive_definite,
    calculate_maximum_sharpe_weights,
    calculate_minimum_variance_weights,
)


class TestAnalyticalEquivalence:
    def test_min_variance_diagonal_matches_closed_form(self):
        variances = np.array([0.01, 0.04, 0.09])
        cov = np.diag(variances)
        expected = (1.0 / variances) / (1.0 / variances).sum()

        weights = calculate_minimum_variance_weights(cov)
        assert np.allclose(weights, expected, atol=1e-12)

    def test_max_sharpe_diagonal_matches_closed_form(self):
        variances = np.array([0.01, 0.04])
        cov = np.diag(variances)
        excess = np.array([0.05, 0.02])
        closed_form = (excess / variances) / (excess / variances).sum()

        weights = calculate_maximum_sharpe_weights(excess, cov, 0.0)
        assert np.allclose(weights, closed_form, atol=1e-12)


class TestStabilityUnderCollinearity:
    def test_severe_collinearity_stays_finite_and_normalized(self, caplog):
        base = np.linspace(-0.01, 0.01, 60)
        near_dup = base + base * 1e-12 + rng_like(60)
        cov = np.cov(np.column_stack([base, base * 2, near_dup]), rowvar=False) + np.eye(3) * 1e-10

        with caplog.at_level(logging.WARNING):
            min_var = calculate_minimum_variance_weights(cov)
            max_sharpe = calculate_maximum_sharpe_weights(np.array([0.1, 0.2, 0.15]), cov, 0.02)

        for weights in (min_var, max_sharpe):
            assert np.all(np.isfinite(weights))
            assert weights.sum() == pytest.approx(1.0, abs=1e-9)

    def test_all_zero_covariance_falls_back_named(self, caplog):
        cov = np.zeros((3, 3))
        with caplog.at_level(logging.WARNING):
            fallback = calculate_minimum_variance_weights(cov)
            fallback2 = calculate_maximum_sharpe_weights(np.ones(3), cov, 0.0)

        assert np.allclose(fallback, [1 / 3] * 3)
        assert np.allclose(fallback2, [1 / 3] * 3)
        flat_messages = " ".join(caplog.messages)
        assert "equal weights" in flat_messages


def rng_like(size: int) -> np.ndarray:
    rng = np.random.default_rng(99)
    return rng.normal(scale=1e-14, size=size)


class TestPositiveDefiniteRepair:
    def test_pd_matrix_is_copied_with_identical_values(self):
        rng = np.random.default_rng(17)
        returns = rng.normal(scale=0.01, size=(120, 4))
        original = np.cov(returns, rowvar=False)

        repaired = _ensure_positive_definite(original)
        assert np.allclose(repaired, original)  # no jitter applied to healthy PD

    def test_psd_matrix_gets_jittered_deterministically(self, caplog):
        col = np.linspace(-0.01, 0.01, 40)
        singular = np.cov(np.column_stack([col, col]), rowvar=False)  # PSD, rank 1

        with caplog.at_level(logging.WARNING):
            _ensure_positive_definite(singular)  # repair happens + is logged
        assert any("repaired with" in m for m in caplog.messages)

        recovered = calculate_minimum_variance_weights(singular)
        assert np.isfinite(recovered).all() and recovered.sum() == pytest.approx(1.0, abs=1e-9)

    def test_zero_matrix_is_irreparable_loud(self):
        with pytest.raises(np.linalg.LinAlgError, match="[Ii]rreparable"):
            _ensure_positive_definite(np.zeros((2, 2)))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
