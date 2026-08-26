"""Shared offline fixtures: synthetic yfinance-shaped batch panels (feat-021)."""


import numpy as np
import pandas as pd
import pytest

import portfolio_engine.data.data_fetch as data_fetch_module


def _build_panel(spec, rows=20, start="2024-01-01"):
    """Build a yfinance-shaped frame: columns MultiIndex(Ticker, Field).

    spec: {ticker: {"days_missing": [row_offsets], "flat": bool, "trailing_nan": int}}

    Drift is deliberately positive (+0.08%/day ≈ +20% annualized) so healthy
    assets survive the minimum-Sharpe screen — characterization must exercise
    downstream stages, not the filter entry.  Randomness seeded per ticker.
    """
    dates = pd.date_range(start=start, periods=rows, freq="D")
    columns = {}
    for ticker, options in spec.items():
        rng = np.random.default_rng(abs(hash(ticker)) % 2**32)
        drift = options.get("drift", 0.0008)
        values = 100.0 * np.exp(np.cumsum(drift + rng.normal(scale=0.01, size=rows)))
        if options.get("flat"):
            values = np.full(rows, 100.0)
        if options.get("trailing_nan"):
            values[-options["trailing_nan"]:] = np.nan

        keep = np.ones(rows, dtype=bool)
        keep[list(options.get("days_missing", []))] = False
        series = pd.Series(values[keep], index=dates[keep])

        # yfinance keeps rows for all dates a given ticker traded; absent
        # dates surface as NaN once frames are combined:
        aligned = series.reindex(dates)
        columns[(ticker, "Adj Close")] = aligned

    return pd.DataFrame(columns)


@pytest.fixture
def patched_batch(monkeypatch):
    """Patch _fetch_batch to return the panel built from `spec` — no network."""

    def _apply(spec, rows=20):
        panel = _build_panel(spec, rows=rows)

        def fake_batch(tickers, start_date, end_date):
            return panel

        monkeypatch.setattr(data_fetch_module, "_fetch_batch", fake_batch)
        return panel

    return _apply


__all__ = ["_build_panel"]
