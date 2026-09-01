"""Market data provider boundary (M3 Strangler seam).

Orchestration depends on this Protocol, never on yfinance directly.
YFinanceProvider delegates to the legacy module functions so existing
callers keep byte-compatible behavior and the batch boundary tests remain
valid. Adds optional parquet cache (feat-038) with deterministic key.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Protocol

from .cache import _atomic_save, _cache_key, _cache_path, _try_load
from .data_fetch import _resolve_window, download_and_calculate_metrics

logger = logging.getLogger(__name__)


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
    """Default adapter — delegation with optional parquet cache (feat-038).

    `cache_dir=None` disables cache entirely (suite offline, CI).
    `refresh_cache=True` forces re-download even when a file exists.
    `use_cache` explicit overrides `cache_dir is not None` default.
    Key: sorted(upper(tickers)) + window start/end + trading_days + v1.
    """

    def __init__(
        self,
        cache_dir: Path | str | None = None,
        refresh_cache: bool = False,
        use_cache: bool | None = None,
    ) -> None:
        self.cache_dir: Path | None = Path(cache_dir) if cache_dir is not None else None
        self.refresh_cache: bool = bool(refresh_cache)
        # use_cache=None → enabled iff cache_dir is set; explicit False disables
        if use_cache is None:
            self.use_cache: bool = self.cache_dir is not None
        else:
            self.use_cache = bool(use_cache) and self.cache_dir is not None

    def fetch_metrics(
        self,
        ticker_symbols: list,
        risk_free_rate: float,
        lookback_years: int,
        trading_days_per_year: int,
    ) -> tuple:
        if not ticker_symbols:
            return {}, {}, {}

        # Cache attempt (only when enabled and not refreshing)
        if self.use_cache and not self.refresh_cache:
            try:
                start, end = _resolve_window(date.today(), lookback_years)
                key = _cache_key(ticker_symbols, start, end, trading_days_per_year)
                assert self.cache_dir is not None  # for pyright, use_cache implies cache_dir
                path = _cache_path(self.cache_dir, key)
                loaded = _try_load(path, risk_free_rate, trading_days_per_year)
                if loaded is not None:
                    logger.info("cache hit: key=%s path=%s", key, path)
                    return loaded
                logger.info("cache miss: key=%s path=%s", key, path)
            except Exception as exc:  # noqa: BLE001 — cache must never break ingestion
                logger.warning("cache lookup failed — falling back to network: err=%s", exc, exc_info=True)

        bundle = download_and_calculate_metrics(
            ticker_symbols,
            risk_free_rate,
            lookback_years,
            trading_days_per_year,
        )

        # Populate cache on success (non-empty) when enabled
        if self.use_cache:
            asset_metrics, historical_prices, price_dates = bundle
            if historical_prices and price_dates:
                try:
                    start, end = _resolve_window(date.today(), lookback_years)
                    key = _cache_key(ticker_symbols, start, end, trading_days_per_year)
                    assert self.cache_dir is not None
                    path = _cache_path(self.cache_dir, key)
                    _atomic_save(historical_prices, price_dates, path)
                    logger.info("cache write: key=%s path=%s", key, path)
                except Exception as exc:  # noqa: BLE001 — write must not raise
                    logger.warning("cache write skipped: err=%s", exc, exc_info=True)

        return bundle
