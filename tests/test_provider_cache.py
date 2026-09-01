"""Cache parquet contract for feat-038 (TDD red first)."""

import logging
from datetime import date

import numpy as np
import pandas as pd

import portfolio_engine.data.data_fetch as data_fetch_module
from portfolio_engine.data.data_fetch import _resolve_window

BASE_INDEX = pd.date_range("2024-01-01", periods=3, freq="D")


def _batch(spec: dict[str, dict[str, list[float]]], index=None):
    columns = {}
    used_index = index if index is not None else BASE_INDEX
    for ticker, fields in spec.items():
        for field_name, values in fields.items():
            columns[(ticker, field_name)] = pd.Series(
                np.asarray(values, dtype=float), index=used_index
            )
    return pd.DataFrame(columns)


def _today() -> date:
    # import inside to allow monkeypatch if needed; but default uses real today
    from datetime import date as _date

    return _date.today()


class TestCacheKeyDeterminism:
    def test_order_invariant_and_trading_days_in_key(self):
        from portfolio_engine.data.cache import _cache_key

        start = date(2020, 1, 2)
        end = date(2025, 1, 1)
        k1 = _cache_key(["WMT", "AAPL"], start, end, 252)
        k2 = _cache_key(["AAPL", "WMT"], start, end, 252)
        k3 = _cache_key(["AAPL", "WMT"], start, end, 365)
        k4 = _cache_key(["aapl", "wmt"], start, end, 252)
        assert k1 == k2
        assert k1 == k4  # upper invariant
        assert k1 != k3

    def test_key_versioned(self):
        from portfolio_engine.data.cache import CACHE_VERSION, _cache_key

        start = date(2020, 1, 2)
        end = date(2025, 1, 1)
        assert CACHE_VERSION == "v1"
        assert len(_cache_key(["A"], start, end, 252)) == 16
        assert all(c in "0123456789abcdef" for c in _cache_key(["A"], start, end, 252))


class TestYFinanceProviderCache:
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

    def test_second_call_same_key_does_not_hit_network(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({
            "AAA": {"Adj Close": [100.0, 101.0, 102.0]},
            "BBB": {"Adj Close": [200.0, 201.0, 202.0]},
        })
        calls = self._patch_fetch(monkeypatch, [both])

        provider = YFinanceProvider(cache_dir=tmp_path)
        m1, p1, d1 = provider.fetch_metrics(["AAA", "BBB"], 0.045, 5, 252)
        assert calls["n"] == 1
        assert set(m1) == {"AAA", "BBB"}
        assert len(list(tmp_path.glob("v1_*.parquet"))) == 1

        m2, p2, d2 = provider.fetch_metrics(["AAA", "BBB"], 0.045, 5, 252)
        assert calls["n"] == 1  # no second network
        assert set(m2) == {"AAA", "BBB"}
        assert np.allclose(p1["AAA"], p2["AAA"])

    def test_refresh_cache_forces_redownload(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({
            "AAA": {"Adj Close": [100.0, 101.0, 102.0]},
        })
        calls = self._patch_fetch(monkeypatch, [both, both])

        provider = YFinanceProvider(cache_dir=tmp_path, refresh_cache=False)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        assert calls["n"] == 1

        provider_refresh = YFinanceProvider(cache_dir=tmp_path, refresh_cache=True)
        before = list(tmp_path.glob("v1_*.parquet"))[0].stat().st_mtime
        import time

        time.sleep(0.02)
        provider_refresh.fetch_metrics(["AAA"], 0.045, 5, 252)
        assert calls["n"] == 2
        after = list(tmp_path.glob("v1_*.parquet"))[0].stat().st_mtime
        assert after >= before

    def test_offline_from_cache_identical_without_network(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({
            "AAA": {"Adj Close": [100.0, 101.0, 102.0]},
            "BBB": {"Adj Close": [200.0, 201.0, 202.0]},
        })
        calls = self._patch_fetch(monkeypatch, [both])
        provider = YFinanceProvider(cache_dir=tmp_path)
        m1, p1, _ = provider.fetch_metrics(["AAA", "BBB"], 0.045, 5, 252)
        assert calls["n"] == 1

        def boom(*a, **k):
            raise AssertionError("no network")

        monkeypatch.setattr(data_fetch_module, "_fetch_batch", boom)
        m2, p2, _ = provider.fetch_metrics(["AAA", "BBB"], 0.045, 5, 252)
        assert set(m2) == {"AAA", "BBB"}
        assert np.allclose(p1["AAA"], p2["AAA"])
        assert np.allclose(p1["BBB"], p2["BBB"])

    def test_corruption_degrades_and_refetches(self, tmp_path, monkeypatch, caplog):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({"AAA": {"Adj Close": [100.0, 101.0, 102.0]}})
        calls = self._patch_fetch(monkeypatch, [both])
        provider = YFinanceProvider(cache_dir=tmp_path)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        assert calls["n"] == 1
        parquet = list(tmp_path.glob("v1_*.parquet"))[0]
        parquet.write_bytes(b"not parquet")

        # second batch for refetch after corruption
        calls2 = self._patch_fetch(monkeypatch, [both])
        # need a fresh provider so it re-reads corrupted file
        # but reuse same tmp_path
        with caplog.at_level(logging.WARNING):
            m2, _, _ = YFinanceProvider(cache_dir=tmp_path).fetch_metrics(["AAA"], 0.045, 5, 252)
        assert set(m2) == {"AAA"}
        assert any("cache corrupt" in m.lower() for m in caplog.messages)
        assert calls2["n"] == 1
        # parquet should have been rewritten valid
        assert parquet.read_bytes()[:4] != b"not "

    def test_cache_dir_none_bypass(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({"AAA": {"Adj Close": [100.0, 101.0, 102.0]}})
        calls = self._patch_fetch(monkeypatch, [both, both])
        provider = YFinanceProvider(cache_dir=None)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        assert calls["n"] == 2
        assert len(list(tmp_path.glob("*.parquet"))) == 0

    def test_zero_tickers_no_fs(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        calls = self._patch_fetch(monkeypatch, [pd.DataFrame()])
        provider = YFinanceProvider(cache_dir=tmp_path)
        m, p, d = provider.fetch_metrics([], 0.045, 5, 252)
        assert m == {} and p == {} and d == {}
        assert calls["n"] == 0
        assert len(list(tmp_path.glob("*.parquet"))) == 0

    def test_cache_miss_different_today_window_still_uses_window(self, tmp_path, monkeypatch):
        # Ensures key derived from _resolve_window not just lookback int.
        # We control today via monkeypatch of _resolve_window indirectly by
        # checking trading_days still separates keys (already tested) — this
        # just smoke-tests the window dependency.
        from portfolio_engine.data.cache import _cache_key

        s1, e1 = _resolve_window(date(2024, 3, 15), 5)
        s2, e2 = _resolve_window(date(2024, 3, 16), 5)
        k1 = _cache_key(["AAA"], s1, e1, 252)
        k2 = _cache_key(["AAA"], s2, e2, 252)
        assert k1 != k2

    def test_use_cache_false_disables_even_with_dir(self, tmp_path, monkeypatch):
        from portfolio_engine.data.provider import YFinanceProvider

        both = _batch({"AAA": {"Adj Close": [100.0, 101.0, 102.0]}})
        calls = self._patch_fetch(monkeypatch, [both, both])
        provider = YFinanceProvider(cache_dir=tmp_path, use_cache=False)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        provider.fetch_metrics(["AAA"], 0.045, 5, 252)
        assert calls["n"] == 2
        # no parquet should exist when use_cache=False
        assert len(list(tmp_path.glob("v1_*.parquet"))) == 0
