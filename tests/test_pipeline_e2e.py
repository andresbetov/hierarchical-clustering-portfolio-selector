"""End-to-end composition tests — whole pipeline via provider injection (M3/M8)."""

import numpy as np
import pytest

from portfolio_engine.app import pipeline as pipeline_module
from portfolio_engine.app.pipeline import generate_complete_analysis_report, main
from portfolio_engine.core.config import PortfolioConfig
from portfolio_engine.core.metrics import (
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_correlation_matrix,
    calculate_covariance_matrix,
    calculate_sharpe_ratio,
    compute_logarithmic_returns,
    construct_returns_matrix,
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

    def test_shrunken_covariance_estimator_end_to_end(self):
        """feat-033: ledoit_wolf covariance flows through HRP allocation
        offline and still yields finite simplex weights."""
        config = PortfolioConfig(
            minimum_sharpe_threshold=0.5,
            maximum_volatility_threshold=10.0,
            weight_allocation_method="hrp",
            covariance_estimator="ledoit_wolf",
            lookback_years=1,
        )
        result = main(TICKERS, config, provider=SyntheticProvider())
        _, filtered_metrics, _, portfolio_weights = result[:4]

        assert set(portfolio_weights) == set(filtered_metrics)
        values = np.array(list(portfolio_weights.values()))
        assert np.all(np.isfinite(values))
        assert values.sum() == pytest.approx(1.0, abs=1e-6)
        assert np.all(values > 0)


def _equal_length_legacy_bundle():
    """Bundle with equal-length prices for the FULL-universe charts.

    Reproduces the legacy-report data flow (feat-028): N=5 filtered assets,
    M=3 selected representatives after cluster pruning — the shape that used
    to crash `_portfolio_summary_metrics` (weights M vs covariance NxN).
    """
    dates = np.datetime64("2024-01-01", "ns") + np.arange(ROWS, dtype="timedelta64[ns]")
    rng = np.random.default_rng(7)

    prices = {}
    for ticker in TICKERS:
        values = 100.0 * np.exp(np.cumsum(0.0008 + rng.normal(scale=0.01, size=ROWS)))
        prices[ticker] = values

    asset_metrics = {}
    for ticker in TICKERS:
        daily = compute_logarithmic_returns(prices[ticker])
        asset_metrics[ticker] = {
            "daily_returns": daily,
            "annual_return": float(calculate_annualized_return(daily)),
            "annual_volatility": float(calculate_annualized_volatility(daily)),
            "sharpe_ratio": calculate_sharpe_ratio(
                float(calculate_annualized_return(daily)),
                float(calculate_annualized_volatility(daily)),
                0.045,
            ),
        }

    filtered_tickers = TICKERS[:5]
    selected_tickers = filtered_tickers[:3]

    filtered_metrics = {t: asset_metrics[t] for t in filtered_tickers}
    optimal_portfolio = {t: asset_metrics[t] for t in selected_tickers}
    portfolio_weights = {t: 1.0 / 3.0 for t in selected_tickers}

    returns_matrix = construct_returns_matrix({t: prices[t] for t in filtered_tickers})
    correlation_matrix = calculate_correlation_matrix(returns_matrix)
    covariance_matrix = calculate_covariance_matrix(returns_matrix)

    return {
        "asset_metrics": asset_metrics,
        "filtered_metrics": filtered_metrics,
        "optimal_portfolio": optimal_portfolio,
        "portfolio_weights": portfolio_weights,
        "corr_matrix": correlation_matrix,
        "cov_matrix": covariance_matrix,
        "prices": prices,
        "dates": {t: dates for t in TICKERS},
        "filtered_tickers": filtered_tickers,
        "selected_tickers": selected_tickers,
    }


class TestLegacyReportGeneration:
    @pytest.fixture
    def legacy_bundle(self):
        return _equal_length_legacy_bundle()

    def test_pruning_path_report_completes_with_sliced_covariance(self, monkeypatch, legacy_bundle):
        """feat-028: legacy (non-hrp) route with M<N must not crash and the
        report must receive the covariance sliced to the selected portfolio."""
        captured = {}

        def fake_main(tickers, config):
            return (
                legacy_bundle["asset_metrics"],
                legacy_bundle["filtered_metrics"],
                legacy_bundle["optimal_portfolio"],
                legacy_bundle["portfolio_weights"],
                legacy_bundle["corr_matrix"],
                legacy_bundle["cov_matrix"],
                legacy_bundle["prices"],
                legacy_bundle["dates"],
            )

        original_plot = pipeline_module.plot_optimal_portfolio_analysis

        def spy(*args, **kwargs):
            captured["kwargs"] = kwargs
            return original_plot(*args, **kwargs)

        monkeypatch.setattr(pipeline_module, "main", fake_main)
        monkeypatch.setattr(pipeline_module, "plot_optimal_portfolio_analysis", spy)

        config = PortfolioConfig(weight_allocation_method="risk_parity", lookback_years=1)
        result = generate_complete_analysis_report(TICKERS, config, save_plots=False, show_plots=False)

        assert captured["kwargs"], "report never reached the optimal-portfolio chart"
        passed_cov = captured["kwargs"]["covariance_matrix"]

        expected_index = [legacy_bundle["filtered_tickers"].index(t) for t in legacy_bundle["selected_tickers"]]
        expected_cov = legacy_bundle["cov_matrix"][np.ix_(expected_index, expected_index)]

        assert passed_cov.shape == (3, 3)
        assert np.allclose(passed_cov, expected_cov)

        _, _, returned_portfolio, returned_weights = result
        assert set(returned_portfolio) == set(legacy_bundle["selected_tickers"])
        assert set(returned_weights) == set(legacy_bundle["selected_tickers"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
