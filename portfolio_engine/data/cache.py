"""Parquet cache helpers for YFinanceProvider (feat-038).

Key: sha256(sorted(upper(tickers)) + start + end + trading_days + v1) -> 16 hex.
Atomic write: mkstemp + pq.write_table(snappy) + os.replace.
Lazy pyarrow import — missing lib degrades to no-cache with warning.
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
)

logger = logging.getLogger(__name__)

CACHE_VERSION = "v1"


def _cache_key(
    ticker_symbols: list[str],
    start_date: date,
    end_date: date,
    trading_days_per_year: int,
) -> str:
    norm = sorted(t.strip().upper() for t in ticker_symbols if t.strip())
    payload = (
        "|".join(norm)
        + f"|{start_date.isoformat()}|{end_date.isoformat()}|{trading_days_per_year}|{CACHE_VERSION}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{CACHE_VERSION}_{key}.parquet"


def _bundle_to_frame(
    historical_prices: dict[str, np.ndarray],
    price_dates: dict[str, pd.DatetimeIndex],
) -> pd.DataFrame:
    """Long format: date (ns), ticker (str), close (float64). Sorted for stability."""
    rows: list[object] = []
    for ticker, prices in historical_prices.items():
        dates = price_dates[ticker]
        for d, v in zip(dates, prices, strict=True):
            ts = pd.Timestamp(d)
            if pd.isna(ts):
                continue
            rows.append((ts, str(ticker), float(v)))  # type: ignore[arg-type]
    if not rows:
        return pd.DataFrame({"date": pd.array([], dtype="datetime64[ns]"), "ticker": [], "close": []})
    df = pd.DataFrame(rows, columns=["date", "ticker", "close"])
    # Ensure dtypes for pyarrow round-trip
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = df["ticker"].astype(str)
    df["close"] = df["close"].astype(np.float64)
    df = df.sort_values(["ticker", "date"], kind="mergesort").reset_index(drop=True)
    return df


def _frame_to_bundle(
    df: pd.DataFrame,
    risk_free_rate: float,
    trading_days_per_year: int,
) -> tuple[dict, dict, dict]:
    """Reconstruct (asset_metrics, historical_prices, price_dates) from long df."""
    if df.empty or "ticker" not in df.columns:
        return {}, {}, {}

    # Validate schema
    if not {"date", "ticker", "close"}.issubset(df.columns):
        raise ValueError(f"cache schema mismatch columns={list(df.columns)}")

    historical_prices: dict[str, np.ndarray] = {}
    price_dates: dict[str, pd.DatetimeIndex] = {}

    for ticker, group in df.groupby("ticker", sort=False):
        g = group.sort_values("date")
        dates = pd.DatetimeIndex(pd.to_datetime(g["date"].values))
        prices = g["close"].to_numpy(dtype=np.float64)
        historical_prices[str(ticker)] = prices
        price_dates[str(ticker)] = dates

    # Recompute metrics (risk_free_rate not in key — fresh value)
    asset_metrics: dict[str, dict] = {}
    for ticker, prices in historical_prices.items():
        daily = compute_logarithmic_returns(prices)
        annual_return = float(calculate_annualized_return(daily, trading_days_per_year))
        annual_vol = float(calculate_annualized_volatility(daily, trading_days_per_year))
        sharpe = calculate_sharpe_ratio(annual_return, annual_vol, risk_free_rate)
        asset_metrics[ticker] = {
            "daily_returns": daily,
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe,
        }

    return asset_metrics, historical_prices, price_dates


def _try_load(
    path: Path,
    risk_free_rate: float,
    trading_days_per_year: int,
) -> tuple[dict, dict, dict] | None:
    """Attempt to load parquet; on corruption warn+unlink and return None."""
    if not path.exists():
        return None
    try:
        import pyarrow.parquet as pq
    except ImportError:
        logger.warning("pyarrow not installed — cache disabled: path=%s", path)
        return None

    try:
        table = pq.read_table(str(path))
        df = table.to_pandas()
        # Basic sanity: must have 3 columns
        if df.empty:
            logger.warning("cache empty — treating as miss: path=%s", path)
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            return None
        return _frame_to_bundle(df, risk_free_rate, trading_days_per_year)
    except (OSError, ValueError, ImportError) as exc:
        # Narrow graceful set: pyarrow ArrowInvalid is OSError subclass; ValueError covers schema
        logger.warning("cache corrupt — refetching: path=%s err=%s", path, exc, exc_info=True)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None
    except Exception as exc:  # noqa: BLE001 — unexpected, surface as warning but still degrade
        logger.warning("cache corrupt — refetching (unexpected): path=%s err=%s", path, exc, exc_info=True)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def _atomic_save(
    historical_prices: dict[str, np.ndarray],
    price_dates: dict[str, pd.DatetimeIndex],
    path: Path,
) -> None:
    """Atomic parquet write with snappy; creation of parent dirs is caller's duty."""
    if not historical_prices:
        return
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        logger.warning("pyarrow not installed — cache write skipped: path=%s", path)
        return

    df = _bundle_to_frame(historical_prices, price_dates)
    if df.empty:
        return

    table = pa.Table.from_pandas(df, preserve_index=False)

    # Ensure parent exists
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("cache dir creation failed — write skipped: path=%s err=%s", path, exc)
        return

    # Atomic write via temp file in same dir
    tmp_fd = None
    tmp_path: Path | None = None
    try:
        tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        os.close(tmp_fd)
        tmp_fd = None
        tmp_path = Path(tmp_name)
        pq.write_table(table, str(tmp_path), compression="snappy")
        os.replace(str(tmp_path), str(path))
        tmp_path = None
    except OSError as exc:
        logger.warning("cache write failed — degraded: path=%s err=%s", path, exc, exc_info=True)
    except Exception as exc:  # noqa: BLE001 — pyarrow write errors
        logger.warning("cache write failed — degraded: path=%s err=%s", path, exc, exc_info=True)
    finally:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
