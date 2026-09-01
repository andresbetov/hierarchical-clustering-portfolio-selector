"""Configuration contract tests (M1)."""

import dataclasses

import pytest

from portfolio_engine.core.config import WEIGHT_ALLOCATION_METHODS, PortfolioConfig


class TestDefaultsValid:
    def test_default_construction_passes_validation(self):
        config = PortfolioConfig()
        assert config.weight_allocation_method == "hrp"
        assert config.lookback_years == 5


class TestImmutability:
    def test_attribute_mutation_rejected(self):
        config = PortfolioConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.minimum_sharpe_threshold = -10.0

    def test_replace_creates_new_instance_not_mutation(self):
        original = PortfolioConfig()
        modified = dataclasses.replace(original, minimum_sharpe_threshold=-10.0)
        assert modified is not original
        assert original.minimum_sharpe_threshold == 0.5  # untouched


class TestValidationRules:
    def test_weights_not_summing_to_one_rejected(self):
        with pytest.raises(ValueError, match="sum to 1"):
            PortfolioConfig(sharpe_weight=0.5, diversification_weight=0.2, volatility_penalty_weight=0.2)

    def test_negative_risk_free_rate_rejected(self):
        with pytest.raises(ValueError, match="risk_free_rate"):
            PortfolioConfig(risk_free_rate=-0.01)

    def test_inverted_weight_bounds_rejected(self):
        with pytest.raises(ValueError, match="minimum_single_asset_weight"):
            PortfolioConfig(minimum_single_asset_weight=0.4, maximum_single_asset_weight=0.3)

    def test_invalid_lookback_rejected(self):
        with pytest.raises(ValueError, match="lookback_years"):
            PortfolioConfig(lookback_years=0)

    @pytest.mark.parametrize("bad_days", [0, 367])
    def test_invalid_trading_days_rejected(self, bad_days):
        with pytest.raises(ValueError, match="trading_days_per_year"):
            PortfolioConfig(trading_days_per_year=bad_days)

    def test_unknown_allocation_method_rejected(self):
        with pytest.raises(ValueError, match="risk_parit"):
            PortfolioConfig(weight_allocation_method="risk_parit")

    def test_method_enum_is_executable_documentation(self):
        assert set(WEIGHT_ALLOCATION_METHODS) == {
            "equal",
            "inverse_volatility",
            "risk_parity",
            "max_sharpe",
            "min_variance",
            "hrp",
        }

    def test_dead_vol_target_parameter_removed_by_adr_001(self):
        """ADR 001 (docs/adr/001-volatility-target-removal.md): vol-targeting
        requires leverage, out of the long-only fully-invested mandate."""
        import dataclasses

        assert not any(f.name == "target_portfolio_volatility" for f in dataclasses.fields(PortfolioConfig))

    def test_replace_pattern_is_the_legal_override_route(self):
        loosened = dataclasses.replace(PortfolioConfig(), minimum_sharpe_threshold=-10.0)
        assert loosened.minimum_sharpe_threshold == -10.0
        # Original untouched (immutability semantics):
        assert PortfolioConfig().minimum_sharpe_threshold == 0.5

    def test_default_covariance_estimator_is_sample(self):
        assert PortfolioConfig().covariance_estimator == "sample"

    def test_unknown_covariance_estimator_rejected(self):
        with pytest.raises(ValueError, match="covariance_estimator"):
            PortfolioConfig(covariance_estimator="shrinkage_otro")

    def test_replace_preserves_covariance_estimator_contract(self):
        config = dataclasses.replace(PortfolioConfig(), covariance_estimator="ledoit_wolf")
        assert config.covariance_estimator == "ledoit_wolf"
        assert PortfolioConfig().covariance_estimator == "sample"

    def test_default_linkage_method_is_single(self):
        assert PortfolioConfig().linkage_method == "single"

    def test_unknown_linkage_method_rejected(self):
        with pytest.raises(ValueError, match="linkage_method"):
            PortfolioConfig(linkage_method="centroid")

    def test_replace_preserves_linkage_method_contract(self):
        config = dataclasses.replace(PortfolioConfig(), linkage_method="ward")
        assert config.linkage_method == "ward"
        assert PortfolioConfig().linkage_method == "single"

    def test_default_overlap_ratio_is_0_9(self):
        assert PortfolioConfig().minimum_overlap_ratio == 0.9

    @pytest.mark.parametrize("bad", [0, 0.0, -0.1, 1.0001, 2.0])
    def test_invalid_overlap_ratio_rejected(self, bad):
        with pytest.raises(ValueError, match="minimum_overlap_ratio"):
            PortfolioConfig(minimum_overlap_ratio=bad)

    def test_overlap_ratio_one_is_valid(self):
        assert PortfolioConfig(minimum_overlap_ratio=1.0).minimum_overlap_ratio == 1.0

    def test_replace_preserves_overlap_ratio_contract(self):
        config = dataclasses.replace(PortfolioConfig(), minimum_overlap_ratio=0.5)
        assert config.minimum_overlap_ratio == 0.5
        assert PortfolioConfig().minimum_overlap_ratio == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
