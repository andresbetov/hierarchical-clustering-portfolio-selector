"""Integration tests for the full pipeline."""
import numpy as np
import pytest

from portfolio_engine import (
    PortfolioConfig,
    apply_asset_filters,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_optimal_portfolio_weights,
    construct_returns_matrix,
    select_optimal_diversified_portfolio,
)


@pytest.fixture
def sample_config():
    """Minimal config for testing."""
    config = PortfolioConfig()
    config.minimum_sharpe_threshold = -10
    config.maximum_volatility_threshold = 10
    config.maximum_correlation_threshold = 0.8
    return config


@pytest.fixture
def synthetic_prices():
    """Generate synthetic price data for offline testing."""
    np.random.seed(42)

    # Create 4 synthetic assets with correlated movements
    asset_1 = 100 * np.exp(np.cumsum(np.random.randn(100) * 0.01))
    asset_2 = 90 * np.exp(np.cumsum(np.random.randn(100) * 0.015))
    asset_3 = 150 * np.exp(np.cumsum(np.random.randn(100) * 0.008))
    asset_4 = 120 * np.exp(np.cumsum(np.random.randn(100) * 0.012))

    return {
        "AAA": asset_1,
        "BBB": asset_2,
        "CCC": asset_3,
        "DDD": asset_4,
    }


class TestPipelineIntegration:
    """Test the full pipeline flow."""

    def test_returns_matrix_construction(self, synthetic_prices):
        """Test that returns matrix is constructed correctly."""
        returns = construct_returns_matrix(synthetic_prices)
        assert returns.shape == (99, 4)  # 100 prices - 1, 4 assets
        assert all(np.isfinite(returns.flat))

    def test_correlation_computation(self, synthetic_prices):
        """Test correlation matrix is valid."""
        returns = construct_returns_matrix(synthetic_prices)
        corr = calculate_correlation_matrix(returns)
        assert corr.shape == (4, 4)
        assert np.allclose(np.diag(corr), 1.0)
        assert np.allclose(corr, corr.T, atol=1e-10)

    def test_covariance_computation(self, synthetic_prices):
        """Test covariance matrix is valid."""
        returns = construct_returns_matrix(synthetic_prices)
        cov = calculate_covariance_matrix(returns)
        assert cov.shape == (4, 4)
        assert np.allclose(cov, cov.T, atol=1e-10)

    def test_filtering_reduces_assets(self, sample_config):
        """Test that filtering actually reduces the asset count."""
        # Create synthetic metrics with varying Sharpe ratios
        metrics = {
            "AAA": {"sharpe_ratio": 1.5, "annual_volatility": 0.1},
            "BBB": {"sharpe_ratio": 0.3, "annual_volatility": 0.2},  # Will be filtered out
            "CCC": {"sharpe_ratio": 0.8, "annual_volatility": 0.15},
        }
        prices = {
            "AAA": np.array([100, 101, 102]),
            "BBB": np.array([100, 101, 102]),
            "CCC": np.array([100, 101, 102]),
        }

        filtered_metrics, _ = apply_asset_filters(
            metrics, prices,
            minimum_sharpe=0.5,
            maximum_volatility=0.18
        )

        # BBB should be filtered for low Sharpe; no change for others
        assert "AAA" in filtered_metrics
        assert "BBB" not in filtered_metrics
        assert "CCC" in filtered_metrics

    def test_portfolio_selection(self, synthetic_prices, sample_config):
        """Test that optimal portfolio is selected."""
        returns = construct_returns_matrix(synthetic_prices)
        corr = calculate_correlation_matrix(returns)

        # Create synthetic asset metrics
        metrics = {
            "AAA": {"sharpe_ratio": 1.2, "annual_volatility": 0.10, "annual_return": 0.15},
            "BBB": {"sharpe_ratio": 0.9, "annual_volatility": 0.12, "annual_return": 0.12},
            "CCC": {"sharpe_ratio": 1.0, "annual_volatility": 0.11, "annual_return": 0.14},
            "DDD": {"sharpe_ratio": 0.7, "annual_volatility": 0.13, "annual_return": 0.10},
        }

        portfolio = select_optimal_diversified_portfolio(corr, metrics, sample_config)

        # Should select at least one asset
        assert len(portfolio) > 0
        assert len(portfolio) <= 4

    def test_weight_allocation(self, synthetic_prices, sample_config):
        """Test that weights are properly allocated."""
        returns = construct_returns_matrix(synthetic_prices)
        corr = calculate_correlation_matrix(returns)
        cov = calculate_covariance_matrix(returns)

        metrics = {
            "AAA": {"sharpe_ratio": 1.2, "annual_volatility": 0.10, "annual_return": 0.15},
            "BBB": {"sharpe_ratio": 0.9, "annual_volatility": 0.12, "annual_return": 0.12},
            "CCC": {"sharpe_ratio": 1.0, "annual_volatility": 0.11, "annual_return": 0.14},
            "DDD": {"sharpe_ratio": 0.7, "annual_volatility": 0.13, "annual_return": 0.10},
        }

        portfolio = select_optimal_diversified_portfolio(corr, metrics, sample_config)

        if len(portfolio) > 0:
            weights = calculate_optimal_portfolio_weights(
                portfolio, corr, cov, metrics, sample_config
            )

            # Weights must sum to 1
            assert np.isclose(sum(weights.values()), 1.0, atol=1e-6)
            # All weights must be positive
            assert all(w > 0 for w in weights.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

