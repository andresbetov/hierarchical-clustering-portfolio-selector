import logging
from datetime import datetime, timedelta

import numpy as np

from ..core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
)

logger = logging.getLogger(__name__)


def download_and_calculate_metrics(ticker_symbols: list, risk_free_rate: float = 0.03):
    """Download 5Y adjusted prices and compute per-asset return/risk metrics.

    Returns:
        tuple[dict, dict, dict]:
        - asset_metrics[ticker] -> daily_returns, annual_return, annual_volatility, sharpe_ratio
        - historical_prices[ticker] -> adjusted close np.ndarray
        - price_dates[ticker] -> datetime index aligned with prices
    """

    # Keep import local so offline/unit tests can import the module without yfinance.
    import yfinance as yf

    end_date = (datetime.today() - timedelta(days=1)).date()
    start_date = end_date - timedelta(days=5 * 365)

    logger.info(
        "Downloading historical prices: tickers=%d window_start=%s window_end=%s",
        len(ticker_symbols),
        start_date,
        end_date,
    )

    historical_prices = {}
    asset_metrics = {}
    price_dates = {}

    for ticker in ticker_symbols:
        try:
            stock_data = yf.Ticker(ticker)
            price_history = stock_data.history(start=start_date, end=end_date, auto_adjust=False)

            adjusted_closing_prices = np.asarray(price_history["Adj Close"].values, dtype=np.float64)
            dates = price_history.index
            historical_prices[ticker] = adjusted_closing_prices
            price_dates[ticker] = dates

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

        except Exception as e:
            logger.warning("Ticker download failed: ticker=%s error=%s", ticker, e)
            continue

    if not asset_metrics:
        logger.warning(
            "No assets were downloaded. Check ticker symbols, network access, or yfinance availability."
        )
    else:
        logger.info("Downloaded assets successfully: downloaded=%d", len(asset_metrics))

    return asset_metrics, historical_prices, price_dates


