"""feat-033 contract tests: covariance estimation seam (ADR 005)."""

import numpy as np
import pytest
from sklearn.covariance import OAS, LedoitWolf

from portfolio_engine.core.metrics import (
    calculate_covariance_matrix,
    estimate_covariance,
)


def _random_returns(n_rows=120, n_assets=8, seed=7):
    rng = np.random.default_rng(seed)
    # Two latent factors + idiosyncratic noise: realistic noisy covariance.
    factors = rng.normal(scale=0.01, size=(n_rows, 2))
    loadings = rng.normal(scale=0.8, size=(2, n_assets))
    return factors @ loadings + rng.normal(scale=0.005, size=(n_rows, n_assets))


class TestSampleMode:
    def test_sample_bit_identical_to_legacy(self):
        returns = _random_returns()
        assert np.array_equal(
            estimate_covariance(returns, "sample"),
            calculate_covariance_matrix(returns),
        )


class TestShrinkageParity:
    @pytest.mark.parametrize("method, estimator_cls", [("ledoit_wolf", LedoitWolf), ("oas", OAS)])
    def test_parity_with_sklearn(self, method, estimator_cls):
        returns = _random_returns()
        expected = estimator_cls().fit(returns).covariance_
        result = estimate_covariance(returns, method)
        assert result.shape == expected.shape
        assert np.allclose(result, expected, atol=1e-12)

    @pytest.mark.parametrize("method", ["ledoit_wolf", "oas"])
    def test_condition_number_not_worse_than_sample(self, method):
        returns = _random_returns(n_rows=40, n_assets=30, seed=3)
        sample = calculate_covariance_matrix(returns)
        shrunk = estimate_covariance(returns, method)
        assert np.linalg.cond(shrunk) <= np.linalg.cond(sample) + 1e-9


class TestDegenerateInputs:
    def test_single_row_returns_nan_matrix_without_sklearn(self):
        returns = np.array([[0.01, 0.02, -0.01]])
        result = estimate_covariance(returns, "ledoit_wolf")
        assert result.shape == (3, 3)
        assert np.all(np.isnan(result))

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="covariance_estimator"):
            estimate_covariance(_random_returns(), "nope")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
