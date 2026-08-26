"""Property-based characterization of algebraic invariants (M8 red).

Hypothesis strategies generate arbitrary valid covariance matrices; every
allocator must keep the output on/near the simplex with hard verification
passing. derandomize keeps CI deterministic.
"""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from portfolio_engine.portfolio.allocation import (
    apply_weight_constraints,
    calculate_minimum_variance_weights,
    calculate_risk_parity_weights,
)
from portfolio_engine.portfolio.hrp import calculate_hrp_weights

settings.register_profile("ci", derandomize=True, max_examples=40, deadline=None)
settings.load_profile("ci")


def _random_pd_covariance(size: int, rng: np.random.Generator) -> np.ndarray:
    """Σ = A·Aᵀ scaled — symmetric positive-definite by construction."""
    factor = rng.normal(scale=0.01, size=(size, size))
    cov = factor @ factor.T + np.eye(size) * 1e-6
    return (cov + cov.T) / 2  # enforce exact symmetry against float drift


SIZE_STRATEGY = st.integers(min_value=2, max_value=25)


@st.composite
def _cov_and_rng(draw):
    size = draw(SIZE_STRATEGY)
    rng = np.random.default_rng(draw(st.integers(0, 2**31 - 1)))
    return _random_pd_covariance(size, rng), size


class TestSimplexInvarianceAllAllocators:
    @given(data=_cov_and_rng())
    def test_hrp_always_on_simplex(self, data):
        cov, _ = data
        weights = calculate_hrp_weights(cov)

        assert np.all(np.isfinite(weights))
        assert (weights > 0).all()
        assert weights.sum() == pytest.approx(1.0, abs=1e-9)

    @given(data=_cov_and_rng())
    def test_min_variance_always_on_simplex(self, data):
        cov, _ = data
        weights = calculate_minimum_variance_weights(cov)

        assert np.all(np.isfinite(weights))
        assert weights.sum() == pytest.approx(1.0, abs=1e-9)

    @given(data=_cov_and_rng())
    def test_risk_parity_always_finite_normalized(self, data):
        cov, _ = data
        weights = calculate_risk_parity_weights(cov)

        assert np.all(np.isfinite(weights))
        assert weights.sum() == pytest.approx(1.0, abs=1e-9)

    @given(
        data=_cov_and_rng(),
        dominance_seed=st.integers(0, 2**31 - 1),
    )
    def test_bounded_solver_respects_bounds_everywhere(self, data, dominance_seed):
        cov, n_assets = data
        rng = np.random.default_rng(dominance_seed)
        raw = rng.dirichlet(np.full(n_assets, 0.5))

        bounded = apply_weight_constraints(raw, 0.02, min(0.6, 1.0 / n_assets * 3))

        assert bounded.max() <= min(0.6, 1.0 / n_assets * 3) + 1e-9
        assert bounded.min() >= 0.02 - 1e-9
        assert bounded.sum() == pytest.approx(1.0, abs=1e-9)


class TestDegenerateFiniteSemantics:
    @given(duplicate_scale=st.floats(min_value=0.0, max_value=0.5))
    def test_duplicate_column_pair_stays_stable(self, duplicate_scale):
        col = np.linspace(-0.01, 0.01, 80)
        matrix = np.column_stack([col, col])
        cov = np.cov(matrix, rowvar=False)

        hrp_weights = calculate_hrp_weights(cov)
        assert np.isfinite(hrp_weights).all()

    def test_near_zero_vol_asset_does_not_explode_filters(self):
        from portfolio_engine.portfolio.selection import apply_asset_filters

        metrics = {
            "FLAT": {"sharpe_ratio": float("nan"), "annual_volatility": 0.0},
            "ALIVE": {"sharpe_ratio": 1.2, "annual_volatility": 0.18},
        }
        prices = {t: np.array([100.0, 101.0]) for t in metrics}
        filtered, _ = apply_asset_filters(metrics, prices, minimum_sharpe=0.5, maximum_volatility=0.25)

        assert set(filtered) == {"ALIVE"}
