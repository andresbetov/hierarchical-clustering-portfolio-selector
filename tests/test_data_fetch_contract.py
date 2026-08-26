"""Offline contract tests for the market-data layer (no network required)."""

import inspect
import logging
from datetime import date

import numpy as np
import pandas as pd
import pytest

import portfolio_engine.data.data_fetch as data_fetch_module
from portfolio_engine.data.data_fetch import (
    _resolve_window,
    download_and_calculate_metrics,
)

BASE_INDEX = pd.date_range("2024-01-01", periods=3, freq="D")


def _batch(spec: dict[str, dict[str, list[float]]], index=None):
    """Build a frame shaped like yfinance.batch output:
    rows = dates, columns = MultiIndex(Ticker, Field)."""
    columns = {}
    used_index = index if index is not None else BASE_INDEX
    for ticker, fields in spec.items():
        for field_name, values in fields.items():
            columns[(ticker, field_name)] = pd.Series(
                np.asarray(values, dtype=float), index=used_index
            )
    return pd.DataFrame(columns)


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
        start, _ = _resolve_window(date(2024, 6, 1), 4)
        assert start == date(2020, 5, 31)  # leap day included exactly once

    def test_feb29_end_clamps_to_feb28_on_non_leap_target(self):
        start, end = _resolve_window(date(2024, 3, 1), 5)
        assert end == date(2024, 2, 29)
        assert start == date(2019, 2, 28)

    def test_invalid_lookback_rejected(self):
        with pytest.raises(ValueError, match="lookback_years"):
            _resolve_window(date(2024, 3, 1), 0)


class TestBatchIngestion:
    """C2: batched request with named rejections, fallback and bounded retry."""

    def _patch_fetch(self, monkeypatch, batches):
        calls = {"n": 0}

        def fake_batch(tickers, start, end):
            result = batches[min(calls["n"], len(batches) - 1)]
            calls["n"] += 1
            if isinstance(result, Exception):
                raise result
            return result

        monkeypatch.setattr(data_fetch_module, "_fetch_batch", fake_batch)
        return calls

    def test_multi_ticker_adj_close_success(self, monkeypatch):
        both = _batch({
            "AAA": {"Adj Close": [100.0, 101.0, 102.0]},
            "BBB": {"Adj Close": [200.0, 201.0, 202.0]},
        })
        self._patch_fetch(monkeypatch, [both])

        metrics, prices, dates = download_and_calculate_metrics(["AAA", "BBB"], 0.045, 5)

        assert set(metrics) == {"AAA", "BBB"}
        assert metrics["AAA"]["annual_volatility"] > 0
        assert len(prices["AAA"]) == 3 and len(dates["AAA"]) == 3
        assert float(prices["BBB"].sum()) == pytest.approx(603.0)

    def test_close_column_fallback_produces_values(self, monkeypatch, caplog):
        only_close = _batch({"CCC": {"Close": [10.0, 11.0, 12.0]}})
        self._patch_fetch(monkeypatch, [only_close])

        with caplog.at_level(logging.WARNING):
            metrics, prices, _ = download_and_calculate_metrics(["CCC"], 0.045, 5)

        assert set(metrics) == {"CCC"}
        assert float(prices["CCC"].sum()) == pytest.approx(33.0)
        assert any("falling back to Close" in m and "CCC" in m for m in caplog.messages)

    def test_no_usable_column_rejects_named_other_proceeds(self, monkeypatch, caplog):
        broken = _batch({"JUNK": {"Volume": [1.0, 2.0, 3.0]}})
        good = _batch({"GOOD": {"Adj Close": [5.0, 6.0, 7.0]}})
        self._patch_fetch(monkeypatch, [pd.concat([broken, good], axis=1)])

        with caplog.at_level(logging.WARNING):
            metrics, _, _ = download_and_calculate_metrics(["JUNK", "GOOD"], 0.045, 5)

        assert set(metrics) == {"GOOD"}
        flat = " ".join(caplog.messages)
        assert ("no_usable_prices" in flat) and ("No usable price column" in flat)

    def test_empty_batch_yields_empty_results_without_raise(self, monkeypatch, caplog):
        self._patch_fetch(monkeypatch, [pd.DataFrame()])

        with caplog.at_level(logging.WARNING):
            metrics, prices, dates = download_and_calculate_metrics(["AAA"], 0.045, 5)

        assert metrics == {} and prices == {} and dates == {}
        assert any("batch_failed_or_empty" in m for m in caplog.messages)

    def test_transient_failures_retried_then_recovered(self, monkeypatch):
        good = _batch(
            {"AAA": {"Adj Close": [100.0, 101.0]}},
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        )
        calls = self._patch_fetch(
            monkeypatch, [ConnectionError("boom"), ConnectionError("boom"), good]
        )

        metrics, _, _ = download_and_calculate_metrics(["AAA"], 0.045, 5)

        assert set(metrics) == {"AAA"}
        assert calls["n"] == 3

    def test_persistent_failure_returns_empty_named(self, monkeypatch, caplog):
        calls = self._patch_fetch(monkeypatch, [RuntimeError("down")])

        with caplog.at_level(logging.WARNING):
            metrics, _, _ = download_and_calculate_metrics(["AAA"], 0.045, 5)

        assert calls["n"] == 3  # MAX_DOWNLOAD_ATTEMPTS exhausted
        assert metrics == {}
        assert any("exhausted attempts" in m for m in caplog.messages)

    def test_nan_trailing_rows_trimmed_with_log(self, monkeypatch, caplog):
        trimmed = _batch({"DDD": {"Adj Close": [100.0, 101.0, np.nan]}})
        self._patch_fetch(monkeypatch, [trimmed])

        with caplog.at_level(logging.INFO):
            _, prices, _ = download_and_calculate_metrics(["DDD"], 0.045, 5)

        assert len(prices["DDD"]) == 2
        assert any("trimmed" in m for m in caplog.messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
