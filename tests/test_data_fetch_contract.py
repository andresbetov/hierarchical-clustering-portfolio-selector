"""Offline contract tests for the market-data layer (no network required)."""

import inspect
from datetime import date

import pytest

from portfolio_engine.data.data_fetch import _resolve_window, download_and_calculate_metrics


class TestRiskFreeRateSourcing:
    """A2: the rate lives ONLY in PortfolioConfig; the fetcher has no default."""

    def test_missing_risk_free_rate_fails_at_binding(self):
        # TypeError at binding time => body (network) never executes.
        with pytest.raises(TypeError):
            download_and_calculate_metrics(["AAPL"])

    def test_no_default_value_survives_in_signature(self):
        sig = inspect.signature(download_and_calculate_metrics)
        assert sig.parameters["risk_free_rate"].default is inspect.Parameter.empty


class TestLookbackSourcing:
    """A4: lookback is explicit, calendar-accurate, and has no local default."""

    def test_missing_lookback_fails_at_binding(self):
        with pytest.raises(TypeError):
            download_and_calculate_metrics(["AAPL"], 0.045)

    def test_no_default_for_lookback_in_signature(self):
        sig = inspect.signature(download_and_calculate_metrics)
        assert sig.parameters["lookback_years"].default is inspect.Parameter.empty


class TestResolveWindow:
    """Pure date logic — deterministic, no network."""

    def test_normal_year_span(self):
        start, end = _resolve_window(date(2024, 3, 15), 5)
        assert end == date(2024, 3, 14)
        assert start == date(2019, 3, 14)

    def test_five_calendar_years_beats_365_multiple(self):
        # 2020 was a leap year: a naive 5*365-day window would lose a day.
        start, _ = _resolve_window(date(2024, 6, 1), 4)
        assert start == date(2020, 5, 31)  # exact calendar span incl. leap day

    def test_feb29_end_clamps_to_feb28_on_non_leap_target(self):
        start, end = _resolve_window(date(2024, 3, 1), 5)
        assert end == date(2024, 2, 29)
        assert start == date(2019, 2, 28)

    def test_invalid_lookback_rejected(self):
        with pytest.raises(ValueError, match="lookback_years"):
            _resolve_window(date(2024, 3, 1), 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
