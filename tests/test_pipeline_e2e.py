"""End-to-end composition tests — whole pipeline via provider injection (M3/M8)."""

import numpy as np
import pytest

from portfolio_engine.app.pipeline import main
from portfolio_engine.core.config import PortfolioConfig
from portfolio_engine.core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
)

TICKERS = ["AAAA", "BBBB", "CCCC", "DDDD", "EEEE", "FFFF"]
ROWS = 20

# Composition spec per ticker; drift keeps healthy assets above Sharpe screen.
SPEC = {
    0: {},                        # AAAA baseline
    1: {"days_missing": [3]},     # BBBB calendar hole
    2: {"trailing_nan": 2},       # CCCC tail trimmed upstream (provider-level)
    3: {"days_missing": [5, 6]},  # DDDD holes
    4: {"flat": True},            # EEEE must be filtered out (non-finite Sharpe)
    5: {"days_missing": [0, 1, 2]},  # FFFF late start
}


def _build_bundle():
    """Synthetic MetricsBundle: same tuple shape YFinanceProvider returns."""
    dates_by_ticker = {}
    prices_by_ticker = {}

    base_dates = np.datetime64("2024-01-01", "ns") + np.arange(ROWS, dtype="timedelta64[ns]")
    rng = np.random.default_rng(2024)

    for col, options in SPEC.items():
        ticker = TICKERS[col]
        drift = 0.0008
        values = 100.0 * np.exp(np.cumsum(drift + rng.normal(scale=0.01, size=ROWS)))
        if options.get("flat"):
            values = np.full(ROWS, 100.0)

        keep = np.ones(ROWS, dtype=bool)
        keep[options.get("days_missing", [])] = False

        series = values[keep]
        index = base_dates[keep]

        if not options.get("flat"):
            daily = compute_logarithmic_returns(series)
            annual_return = float(calculate_annualized_return(daily))
            annual_vol = float(calculate_annualized_volatility(daily))

        prices_by_ticker[ticker] = series.astype(np.float64)
        dates_by_ticker[ticker] = index

        if "asset_metrics" not in dir() or True:
            pass

    # Build asset_metrics on second pass so flat asset still enters (filter removes it later):
    risk_free_rate = 0.045
    asset_metrics = {}
    for ticker in TICKERS:
        series = prices_by_ticker[ticker]
        daily = compute_logarithmic_returns(series)
        annual_return = float(calculate_annualized_return(daily))
        annual_vol = float(calculate_annualized_volatility(daily))
        sharpe = calculate_sharpe_ratio(annual_return, annual_vol, risk_free_rate)
        asset_metrics[ticker] = {
            "daily_returns": daily,
            "annual_return": annual_return,
            "annual_volatility": annual_vol,
            "sharpe_ratio": sharpe,
        }

    return asset_metrics, prices_by_ticker, dates_by_ticker


class SyntheticProvider:
    """Structural MarketDataProvider over an offline synthetic bundle."""

    def __init__(self, bundle=None):
        self.bundle = bundle or _build_bundle()

    def fetch_metrics(self, ticker_symbols, risk_free_rate, lookback_years, trading_days_per_year):
        return self.bundle


@pytest.fixture
def e2e_result():
    config = PortfolioConfig(
        minimum_sharpe_threshold=0.5,
        maximum_volatility_threshold=10.0,
        weight_allocation_method="hrp",
        lookback_years=1,
    )
    result = main(TICKERS, config, provider=SyntheticProvider())
    return result, config


class TestInjectedComposition:
    def test_flat_asset_excluded_by_named_filter(self, e2e_result):
        result, _ = e2e_result
        all_metrics, filtered_metrics = result[0], result[1]

        assert all_metrics["EEEE"]["annual_volatility"] == 0.0  # truly flat
        assert "EEEE" not in filtered_metrics                    # excluded named
        assert set(filtered_metrics) <= set(TICKERS)

    def test_matrices_square_symmetric_when_universe_viable(self, e2e_result):
        result, _ = e2e_result
        _, filtered_metrics, _, _, corr_matrix, cov_matrix = (result[i] for i in range(6))

        n = len(filtered_metrics)
        assert n >= 2, f"healthy assets should survive drift screen; got {n}"
        assert corr_matrix.shape == (n, n)
        assert cov_matrix.shape == (n, n)
        assert np.allclose(corr_matrix, corr_matrix.T)
        assert np.allclose(cov_matrix, cov_matrix.T)

    def test_hrp_weights_simplex_and_bounds_regimes(self, e2e_result):
        result, config = e2e_result
        _, filtered_metrics, _, portfolio_weights = result[:4]

        assert set(portfolio_weights) == set(filtered_metrics)
        total = sum(portfolio_weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)

        n = len(filtered_metrics)
        effective_max = (
            config.maximum_single_asset_weight
            if n * config.maximum_single_asset_weight >= 1.0
            else 1.0 / n  # relaxation regime for tiny universes
        )
        for weight in portfolio_weights.values():
            assert np.isfinite(weight)
            assert weight > 0
            assert weight <= effective_max + 1e-6

    def test_prices_dates_contract_full_universe_for_charts(self, e2e_result):
        """main() deliberately returns FULL-universe prices/dates for charts;
        stats matrices cover only the filtered+aligned universe."""
        result, _ = e2e_result
        _, filtered_metrics, _, _, _, _, prices, dates = result

        assert set(prices) == set(dates) == set(TICKERS)
        assert set(filtered_metrics) <= set(prices)
        for ticker, series in prices.items():
            assert len(series) == len(dates[ticker])
            assert np.isfinite(series).any()

    def test_provider_dependency_injection_truly_used(self, e2e_result):
        """The injected provider's bundle flows through unchanged."""
        result, _ = e2e_result
        injected_bundle = _build_bundle()
        injected_main = main(TICKERS, PortfolioConfig(), provider=SyntheticProvider(injected_bundle))

        # Same bundle identity ends up returned:
        assert injected_main[6] is injected_bundle[1]
        assert injected_main[7] is injected_bundle[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
