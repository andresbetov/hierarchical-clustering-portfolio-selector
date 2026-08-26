"""Market data provider boundary (M3 Strangler seam).

Orchestration depends on this Protocol, never on yfinance directly.
YFinanceProvider delegates to the legacy module functions so existing
callers keep byte-compatible behavior and the batch boundary tests remain
valid.
"""

from typing import Protocol

from .data_fetch import download_and_calculate_metrics


class MarketDataProvider(Protocol):
    """Structural contract: anything with `fetch_metrics` qualifies.

    Returns `(asset_metrics, historical_prices, price_dates)` — the exact
    tuple shape of the legacy ingestion flow.
    """

    def fetch_metrics(
        self,
        ticker_symbols: list,
        risk_free_rate: float,
        lookback_years: int,
        trading_days_per_year: int,
    ) -> tuple:
        ...


class YFinanceProvider:
    """Default adapter — pure delegation to the proven ingestion flow."""

    def fetch_metrics(
        self,
        ticker_symbols: list,
        risk_free_rate: float,
        lookback_years: int,
        trading_days_per_year: int,
    ) -> tuple:
        return download_and_calculate_metrics(
            ticker_symbols,
            risk_free_rate,
            lookback_years,
            trading_days_per_year,
        )
