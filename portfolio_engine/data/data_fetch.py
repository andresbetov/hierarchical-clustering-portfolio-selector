import logging
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from ..core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
)

logger = logging.getLogger(__name__)

# C2: bounded transport retries for transient batch failures (e.g. sporadic
# YFRateLimitError). Deliberately stdlib-based — tenacity is deferred until
# retry strategies grow beyond this simple policy.
MAX_DOWNLOAD_ATTEMPTS = 3
_RETRY_BACKOFF_SECONDS = (1.0, 2.0)


def _resolve_window(today: date, lookback_years: int) -> tuple[date, date]:
    """Resolve (start, end) download bounds in exact calendar years.

    end = today - 1 day; start = same month/day `lookback_years` earlier.
    Feb-29 endpoints clamp to Feb-28 when the target year is not a leap year.
    Pure function — no network, no global state.
    """
    if lookback_years < 1:
        raise ValueError(f"lookback_years must be >= 1, got {lookback_years}")

    end = today - timedelta(days=1)
    try:
        start = end.replace(year=end.year - lookback_years)
    except ValueError:  # Feb-29 on a non-leap target year
        start = end.replace(year=end.year - lookback_years, day=28)
    return start, end


def _fetch_batch(ticker_symbols: list, start_date: date, end_date: date):
    """Single network call downloading the whole universe unadjusted.

    Kept as a module-level indirection so tests can monkeypatch it offline.
    Returns the raw yfinance frame (MultiIndex columns when N>1 tickers).
    """
    # Keep import local so offline/unit tests can import the module without yfinance.
    import yfinance as yf

    return yf.download(
        tickers=list(ticker_symbols),
        start=start_date,
        end=end_date,
        auto_adjust=False,  # explicit: we rely on the Adj Close column
        progress=False,
        group_by="ticker",
    )


def _download_with_retry(ticker_symbols: list, start_date: date, end_date: date):
    """Batch download with bounded retries; returns None after exhaustion."""
    last_error: Exception | None = None
    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            frame = _fetch_batch(ticker_symbols, start_date, end_date)
            if attempt > 1:
                logger.info("Batch download recovered on attempt %d", attempt)
            return frame
        except Exception as exc:  # noqa: BLE001 — transport layer, reason is logged
            last_error = exc
            logger.warning(
                "Batch download attempt %d/%d failed: error=%s",
                attempt,
                MAX_DOWNLOAD_ATTEMPTS,
                exc,
            )
            if attempt < MAX_DOWNLOAD_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF_SECONDS[min(attempt - 1, len(_RETRY_BACKOFF_SECONDS) - 1)])

    logger.warning(
        "Batch download exhausted attempts: attempts=%d tickers=%d last_error=%s",
        MAX_DOWNLOAD_ATTEMPTS,
        len(ticker_symbols),
        last_error,
    )
    return None


def _extract_adjusted_close(frame: pd.DataFrame, ticker: str):
    """Extract (values, dates_index) for one ticker from a batch frame.

    Column policy: prefer `Adj Close`; fall back to `Close` with a named
    warning; reject otherwise. Handles both MultiIndex (N>1 tickers) and
    flat single-ticker frames. Trailing/partial NaNs are dropped with a log.

    Returns (values: np.ndarray, index: pd.DatetimeIndex) or None when the
    ticker must be rejected (reason already logged).
    """
    try:
        panel = frame[ticker]
    except (KeyError, TypeError):
        logger.warning("Ticker missing from batch response: ticker=%s", ticker)
        return None

    if not isinstance(panel, pd.DataFrame):
        logger.warning("Unexpected batch slice type: ticker=%s type=%s", ticker, type(panel).__name__)
        return None

    if len(panel) == 0:
        logger.warning("Empty price frame rejected: ticker=%s rows=%d", ticker, 0)
        return None

    if "Adj Close" in panel.columns:
        series = panel["Adj Close"]
    elif "Close" in panel.columns:
        logger.warning(
            "Adj Close column unavailable — falling back to Close: ticker=%s "
            "(dividends/splits will NOT be reflected)",
            ticker,
        )
        series = panel["Close"]
    else:
        available = list(panel.columns)
        logger.warning("No usable price column: ticker=%s columns=%s", ticker, available)
        return None

    before_rows = len(series)
    series = series.dropna()
    trimmed = before_rows - len(series)
    if trimmed > 0:
        logger.info("Trailing NaN rows trimmed: ticker=%s trimmed=%d kept=%d", ticker, trimmed, len(series))
    if len(series) == 0:
        logger.warning("Series empty after NaN trim: ticker=%s", ticker)
        return None

    values = np.asarray(series.to_numpy(), dtype=np.float64)
    index = pd.DatetimeIndex(series.index)
    return values, index


def download_and_calculate_metrics(
    ticker_symbols: list,
    risk_free_rate: float,
    lookback_years: int,
):
    """Download adjusted prices over an explicit calendar window and compute
    per-asset return/risk metrics.

    Both `risk_free_rate` and `lookback_years` are REQUIRED — their single
    sources of truth are PortfolioConfig attributes; no local defaults exist
    on purpose.

    Ingestion contract (C2): one batched request; per-ticker extraction with
    Adj Close→Close fallback; all rejections aggregated into a single warning;
    transient failures retried with bounded backoff. Never raises for
    per-ticker data problems — failures are visible in logs and reflected by
    the tickers missing from the result.

    Returns:
        tuple[dict, dict, dict]:
        - asset_metrics[ticker] -> daily_returns, annual_return, annual_volatility, sharpe_ratio
        - historical_prices[ticker] -> adjusted close np.ndarray
        - price_dates[ticker] -> datetime index aligned with prices
    """

    start_date, end_date = _resolve_window(datetime.today().date(), lookback_years)

    logger.info(
        "Downloading historical prices: tickers=%d window_start=%s window_end=%s mode=batch",
        len(ticker_symbols),
        start_date,
        end_date,
    )

    historical_prices = {}
    asset_metrics = {}
    price_dates = {}
    rejections: list[str] = []

    raw_frame = _download_with_retry(ticker_symbols, start_date, end_date)

    if raw_frame is None or len(raw_frame) == 0:
        rejections.extend(f"{ticker}:batch_failed_or_empty" for ticker in ticker_symbols)
    else:
        for ticker in ticker_symbols:  # preserve caller's insertion order
            extracted = _extract_adjusted_close(raw_frame, ticker)
            if extracted is None:
                rejections.append(f"{ticker}:no_usable_prices")
                continue

            adjusted_closing_prices, dates_index = extracted
            historical_prices[ticker] = adjusted_closing_prices
            price_dates[ticker] = dates_index

            daily_log_returns = compute_logarithmic_returns(adjusted_closing_prices)
            annual_return = float(calculate_annualized_return(daily_log_returns))
            annual_volatility = float(calculate_annualized_volatility(daily_log_returns))
            sharpe_ratio = calculate_sharpe_ratio(annual_return, annual_volatility, risk_free_rate)

            asset_metrics[ticker] = {
                "daily_returns": daily_log_returns,
                "annual_return": annual_return,
                "annual_volatility": annual_volatility,
                "sharpe_ratio": sharpe_ratio,
            }

    if rejections:
        logger.warning(
            "Data ingestion rejections: count=%d reasons=%s",
            len(rejections),
            rejections,
        )

    if not asset_metrics:
        logger.warning(
            "No assets were downloaded. Check ticker symbols, network access, or yfinance availability."
        )
    else:
        logger.info("Downloaded assets successfully: downloaded=%d", len(asset_metrics))

    return asset_metrics, historical_prices, price_dates
