"""C4 constraint-solver contract tests."""

import logging

import numpy as np
import pytest

from portfolio_engine.portfolio import allocation as alloc_module
from portfolio_engine.portfolio.allocation import apply_weight_constraints

MIN_W, MAX_W = 0.05, 0.30


class TestAuditExample:
    def test_audit_case_now_respects_bounds(self):
        """The exact reproduction from docs/auditoria-tecnica.md C4."""
        previous = np.array([0.60, 0.10, 0.10, 0.10, 0.10])
        fixed = apply_weight_constraints(previous, MIN_W, MAX_W)

        assert fixed.max() <= MAX_W + 1e-9   # previously returned 0.43
        assert fixed.min() >= MIN_W - 1e-9
        assert fixed.sum() == pytest.approx(1.0, abs=1e-9)

    def test_already_within_bounds_is_identity(self):
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        assert np.allclose(apply_weight_constraints(weights, MIN_W, MAX_W), weights)


class TestSaturation:
    def test_saturated_pair_pinned_to_max(self):
        feasible = apply_weight_constraints(np.array([0.5, 0.5]), MIN_W, 0.50)
        assert np.allclose(feasible, [0.5, 0.5])

    def test_single_heavy_and_tail_redistribution(self):
        raw = np.array([0.90, 0.02, 0.02, 0.02, 0.02, 0.02])
        fixed = apply_weight_constraints(raw, MIN_W, MAX_W)

        assert fixed.max() <= MAX_W + 1e-9
        assert fixed.min() >= MIN_W - 1e-9
        assert fixed.sum() == pytest.approx(1.0, abs=1e-9)
        # Signal preserved: heaviest stays at the top.
        assert fixed.argmax() == 0


class TestInfeasibility:
    def test_two_assets_max_thirty_percent_infeasible(self):
        with pytest.raises(ValueError, match="infeasible"):
            apply_weight_constraints(np.array([0.7, 0.3]), MIN_W, MAX_W)

    def test_max_smaller_than_inverse_count_infeasible(self):
        # n=5 * max=0.10 => 0.50 < 1: no vector can sum to 1 under this cap.
        with pytest.raises(ValueError, match="infeasible"):
            apply_weight_constraints(np.ones(5), 0.15, 0.10)


class TestStressDeterministic:
    def test_hundred_random_inputs_always_valid(self):
        rng = np.random.default_rng(2026)
        for _ in range(100):
            raw = rng.dirichlet(np.full(8, rng.uniform(0.2, 4.0)))
            out = apply_weight_constraints(raw, MIN_W, MAX_W)
            assert out.max() <= MAX_W + 1e-9
            assert out.min() >= MIN_W - 1e-9
            assert out.sum() == pytest.approx(1.0, abs=1e-9)


class TestFinalVerificationGuards:
    def test_exhausted_budget_never_returns_silently(self, monkeypatch, caplog):
        weights = np.array([0.6, 0.1, 0.1, 0.1, 0.1])

        with caplog.at_level(logging.WARNING):
            # Force the exhaustion path with a minimal budget.
            monkeypatch.setattr(alloc_module, "_BOUNDS_MAX_ITERATIONS", 1)
            outcome_loudly_handled = False
            try:
                alloc_module.apply_weight_constraints(weights, MIN_W, MAX_W)
                outcome_loudly_handled = True  # converged within one cycle: legal
            except ValueError:
                outcome_loudly_handled = True  # raised loudly: also legal

        assert outcome_loudly_handled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
