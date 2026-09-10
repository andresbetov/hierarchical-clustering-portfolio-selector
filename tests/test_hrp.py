"""C1 keystone contract tests: canonical HRP behavior."""

import numpy as np
import pytest

from portfolio_engine.core.config import WEIGHT_ALLOCATION_METHODS, PortfolioConfig
from portfolio_engine.portfolio.allocation import calculate_optimal_portfolio_weights_hrp
from portfolio_engine.portfolio.hrp import calculate_hrp_weights


class TestConfigContract:
    def test_hrp_is_default_per_adr003(self):
        assert PortfolioConfig().weight_allocation_method == "hrp"

    def test_hrp_in_enum(self):
        assert "hrp" in WEIGHT_ALLOCATION_METHODS


class TestAnalyticalExpectations:
    def test_two_assets_exact_inverse_variance(self):
        cov = np.diag([0.01, 0.04])
        weights = calculate_hrp_weights(cov)
        # Singleton clusters: alpha reduces to inverse-variance across them.
        assert weights[0] == pytest.approx(0.80, abs=1e-12)
        assert weights[1] == pytest.approx(0.20, abs=1e-12)

    def test_three_assets_sum_and_positivity(self):
        rng = np.random.default_rng(5)
        returns = rng.normal(scale=0.01, size=(200, 3))
        cov = np.cov(returns, rowvar=False)
        weights = calculate_hrp_weights(cov)

        assert np.all(weights > 0)
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)


class TestStructuralProperties:
    def test_permutation_invariance_of_weight_multiset(self):
        rng = np.random.default_rng(21)
        returns = rng.normal(scale=0.01, size=(150, 6))
        cov = np.cov(returns, rowvar=False)

        permutation = [3, 0, 5, 2, 4, 1]
        permuted_cov = cov[np.ix_(permutation, permutation)]

        base = np.sort(calculate_hrp_weights(cov))
        permuted = np.sort(calculate_hrp_weights(permuted_cov))

        assert np.allclose(base, permuted, atol=1e-10)

    def test_quasi_diag_places_blocks_contiguously(self):
        """Structured fixture: two latent factors drive two blocks of assets.

        Quasi-diagonalization must keep each block contiguous and put
        intra-block neighbors (highly correlated) next to each other.
        """
        rng = np.random.default_rng(3)
        n_per_block = 4
        factor_a = rng.normal(scale=0.01, size=(250,))
        factor_b = rng.normal(scale=0.01, size=(250,))
        columns = []
        for _ in range(n_per_block):
            columns.append(factor_a * 0.8 + rng.normal(scale=0.003, size=(250,)))
        for _ in range(n_per_block):
            columns.append(factor_b * 0.8 + rng.normal(scale=0.003, size=(250,)))
        returns = np.column_stack(columns)
        cov = np.cov(returns, rowvar=False)
        corr = cov / np.outer(np.sqrt(np.diag(cov)), np.sqrt(np.diag(cov)))

        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import squareform

        from portfolio_engine.portfolio.hrp import _leaf_order

        distance = np.sqrt(np.maximum(0.5 * (1 - corr), 0))
        np.fill_diagonal(distance, 0)
        link = linkage(squareform(distance, checks=False), method="single")
        order = _leaf_order(link, 2 * n_per_block)

        # Contiguity: every asset sits at most n_per_block-1 away from any
        # other member of its own factor block (block never interleaved).
        positions = {asset: pos for pos, asset in enumerate(order)}
        for left in range(n_per_block):
            for right in range(n_per_block, 2 * n_per_block):
                assert abs(positions[left] - positions[right]) >= 1

        block_positions = [positions[a] for a in range(n_per_block)]
        assert max(block_positions) - min(block_positions) <= n_per_block

        # Intra-ordered adjacency beats the global off-diagonal mean.
        reordered = corr[np.ix_(order, order)]
        adjacent = np.mean([abs(reordered[i, i + 1]) for i in range(len(order) - 1)])
        global_mean_abs = np.abs(corr[np.triu_indices(len(order), 1)]).mean()
        assert adjacent > global_mean_abs


class TestDegenerateInputs:
    def test_duplicate_columns_finite_equal_half(self):
        col = np.linspace(-0.01, 0.01, 50) ** 2
        cov = np.cov(np.column_stack([col, col]), rowvar=False)
        weights = calculate_hrp_weights(cov)

        assert np.all(np.isfinite(weights))
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)
        assert weights[0] == pytest.approx(0.5, abs=1e-9)  # perfect twins split evenly

    def test_non_finite_covariance_rejected_loudly(self):
        cov = np.array([[0.01, np.nan], [np.nan, 0.04]])
        with pytest.raises(ValueError, match="non-finite"):
            calculate_hrp_weights(cov)

    def test_negative_variance_rejected(self):
        with pytest.raises(ValueError, match="non-positive"):
            calculate_hrp_weights(np.array([[0.01, 0.0], [0.0, -0.02]]))


class TestLinkageParameter:
    """feat-034 (ADR 006): linkage parametrizable, single keeps the snapshot."""

    def _three_block_cov(self, n_per_block=2, seed=19):
        """3 independent latent factors, one per block: intra-block corr high,
        inter-block corr ~0. Returns (cov, corr) for 3*n_per_block assets."""
        rng = np.random.default_rng(seed)
        columns = []
        for _ in range(3):
            factor = rng.normal(scale=0.01, size=(250,))
            for _ in range(n_per_block):
                columns.append(factor * 0.9 + rng.normal(scale=0.003, size=(250,)))
        returns = np.column_stack(columns)
        cov = np.cov(returns, rowvar=False)
        corr = cov / np.outer(np.sqrt(np.diag(cov)), np.sqrt(np.diag(cov)))
        return cov, corr

    def test_default_single_preserves_snapshot(self):
        """No linkage_method => weights identical to the legacy call (snapshot)."""
        cov, _ = self._three_block_cov()
        assert np.array_equal(
            calculate_hrp_weights(cov),
            calculate_hrp_weights(cov, linkage_method="single"),
        )

    def test_ward_yields_valid_weights_and_adjacent_blocks(self):
        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import squareform

        from portfolio_engine.portfolio.hrp import _leaf_order

        cov, corr = self._three_block_cov()
        weights = calculate_hrp_weights(cov, linkage_method="ward")

        assert np.all(np.isfinite(weights))
        assert np.all(weights > 0)
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)

        distance = np.sqrt(np.maximum(0.5 * (1 - corr), 0))
        np.fill_diagonal(distance, 0)
        link = linkage(squareform(distance, checks=False), method="ward")
        order = _leaf_order(link, 6)

        for block_start in (0, 2, 4):
            positions = [order.index(block_start), order.index(block_start + 1)]
            assert abs(positions[0] - positions[1]) == 1  # block members adjacent

    def test_average_yields_valid_weights(self):
        cov, _ = self._three_block_cov()
        weights = calculate_hrp_weights(cov, linkage_method="average")

        assert np.all(np.isfinite(weights))
        assert np.all(weights > 0)
        assert weights.sum() == pytest.approx(1.0, abs=1e-12)

    def test_unknown_linkage_raises(self):
        cov, _ = self._three_block_cov()
        with pytest.raises(ValueError, match="linkage"):
            calculate_hrp_weights(cov, linkage_method="centroid")


class TestEndToEndWrapper:
    def _metrics(self, tickers):
        return {
            t: {"sharpe_ratio": 1.0, "annual_volatility": 0.15, "annual_return": 0.1}
            for t in tickers
        }

    def test_wrapper_respects_bounds_and_single_asset_route(self):
        config = PortfolioConfig()
        rng = np.random.default_rng(77)
        returns = rng.normal(scale=0.01, size=(180, 5))
        cov = np.cov(returns, rowvar=False)

        weights = calculate_optimal_portfolio_weights_hrp(self._metrics(list("ABCDE")), cov, config)

        assert set(weights) == set("ABCDE")   # every filtered asset allocated
        assert all(w > 0 for w in weights.values())
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-9)
        assert max(weights.values()) <= config.maximum_single_asset_weight + 1e-9

    def test_empty_and_single_routes(self):
        config = PortfolioConfig()
        assert calculate_optimal_portfolio_weights_hrp({}, np.zeros((0, 0)), config) == {}

        single = calculate_optimal_portfolio_weights_hrp(
            self._metrics(["SOLO"]), np.array([[0.02]]), config
        )
        assert single == {"SOLO": 1.0}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
