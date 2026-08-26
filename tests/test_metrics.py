"""Core metrics unit tests."""

import numpy as np
import pytest

from portfolio_engine.core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
    construct_returns_matrix,
)


class TestLogarithmicReturns:
    """Test log return computation."""

    def test_basic_returns(self):
        prices = np.array([100.0, 101.0, 102.0, 103.0])
        returns = compute_logarithmic_returns(prices)
        assert len(returns) == 3
        assert returns[0] > 0  # 101/100 > 1
        assert all(np.isfinite(returns))

    def test_empty_series(self):
        prices = np.array([100.0])
        returns = compute_logarithmic_returns(prices)
        assert len(returns) == 0

    def test_constant_price(self):
        prices = np.array([100.0, 100.0, 100.0])
        returns = compute_logarithmic_returns(prices)
        assert np.allclose(returns, 0.0)


class TestAnnualizedMetrics:
    """Test annualization of returns and volatility."""

    def test_annualized_return(self):
        # Daily return of 0.1% annualizes to ~25% (0.001 * 252)
        daily_returns = np.array([0.001] * 252)
        annual_return = calculate_annualized_return(daily_returns)
        assert np.isclose(annual_return, 0.252, atol=0.001)

    def test_annualized_volatility(self):
        # Sample estimator (ddof=1) consistent with the covariance kernel (C3).
        daily_returns = np.array([0.01, -0.01] * 126)
        expected = float(np.std(daily_returns, ddof=1)) * np.sqrt(252)
        annual_vol = calculate_annualized_volatility(daily_returns)
        assert annual_vol == pytest.approx(expected, rel=1e-12)

    def test_sharpe_ratio(self):
        annual_return = 0.10  # 10%
        annual_vol = 0.15  # 15%
        risk_free = 0.02  # 2%
        sharpe = calculate_sharpe_ratio(annual_return, annual_vol, risk_free)
        expected = (0.10 - 0.02) / 0.15
        assert np.isclose(sharpe, expected)


class TestNumericGuards:
    """C3: degenerate inputs produce NaN semantics and never infinities."""

    def test_sharpe_nan_for_zero_volatility(self):
        assert np.isnan(calculate_sharpe_ratio(0.10, 0.0, 0.02))

    def test_sharpe_nan_for_tiny_below_eps(self):
        assert np.isnan(calculate_sharpe_ratio(0.10, 1e-15, 0.02))

    def test_sharpe_finite_for_small_positive_vol(self):
        assert np.isfinite(calculate_sharpe_ratio(0.10, 1e-6, 0.02))

    def test_volatility_single_point_is_nan_not_crash(self):
        assert np.isnan(calculate_annualized_volatility(np.array([0.01])))

    def test_correlation_diagonal_honest_for_flat_asset(self):
        flat = np.full((30,), 0.001)  # zero variance daily series
        varying = np.linspace(-0.02, 0.02, 30)
        matrix = calculate_correlation_matrix(np.column_stack([varying, flat]))

        assert np.isnan(matrix[1, 1])  # no fake 1.0 for a flat asset
        assert np.isnan(matrix[0, 1])
        assert np.isnan(matrix[1, 0])
        assert matrix[0, 0] == 1.0  # informative asset keeps honest diagonal

    def test_covariance_singular_dup_columns_still_finite(self):
        col = np.linspace(-0.01, 0.01, 40)
        matrix = calculate_covariance_matrix(np.column_stack([col, col]))
        assert np.all(np.isfinite(matrix))
        assert np.allclose(matrix, matrix.T)


class TestCorrelationMatrix:
    """Test correlation matrix computation."""

    def test_perfect_correlation(self):
        # Two assets with identical returns
        returns = np.array(
            [
                [1.0, 2.0, 3.0],
                [1.0, 2.0, 3.0],
            ]
        ).T  # Shape: (3, 2)
        corr = calculate_correlation_matrix(returns)
        assert corr.shape == (2, 2)
        assert np.isclose(corr[0, 1], 1.0)
        assert np.isclose(corr[1, 0], 1.0)

    def test_uncorrelated_assets(self):
        # Independent random returns
        np.random.seed(42)
        returns = np.random.randn(100, 3)
        corr = calculate_correlation_matrix(returns)
        assert corr.shape == (3, 3)
        assert np.allclose(np.diag(corr), 1.0)  # Diagonal is 1
        assert np.allclose(corr, corr.T)  # Symmetric


class TestCovarianceMatrix:
    """Test covariance matrix computation."""

    def test_covariance_shape(self):
        returns = np.random.randn(50, 4)
        cov = calculate_covariance_matrix(returns)
        assert cov.shape == (4, 4)
        assert np.allclose(cov, cov.T)  # Symmetric


class TestReturnsMatrix:
    """Test construction of returns matrix from price dict."""

    def test_returns_matrix_shape(self):
        prices = {
            "AAPL": np.array([100.0, 101.0, 102.0, 103.0]),
            "MSFT": np.array([200.0, 202.0, 204.0, 206.0]),
            "GOOGL": np.array([1500.0, 1510.0, 1520.0, 1530.0]),
        }
        returns = construct_returns_matrix(prices)
        # Should be (3 prices - 1, 3 assets) = (3, 3)
        assert returns.shape == (3, 3)
        assert all(np.isfinite(returns.flat))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
