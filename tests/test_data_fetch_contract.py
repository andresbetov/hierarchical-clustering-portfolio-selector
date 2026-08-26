"""Offline contract tests for the market-data layer (no network required)."""

import pytest

from portfolio_engine.data.data_fetch import download_and_calculate_metrics


class TestRiskFreeRateSourcing:
    """A2: the rate lives ONLY in PortfolioConfig; the fetcher has no default."""

    def test_missing_risk_free_rate_fails_at_binding(self):
        # TypeError at binding time => body (network) never executes.
        with pytest.raises(TypeError):
            download_and_calculate_metrics(["AAPL"])

    def test_no_default_value_survives_in_signature(self):
        import inspect

        sig = inspect.signature(download_and_calculate_metrics)
        param = sig.parameters["risk_free_rate"]
        assert param.default is inspect.Parameter.empty
