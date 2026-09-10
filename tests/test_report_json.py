"""TDD red-first contract tests for the technical report JSON core (feat-043)."""

import dataclasses
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest


def _raise_constant(value):
    raise ValueError(f"non-standard JSON constant in report: {value}")


def _strict_loads(text):
    return json.loads(text, parse_constant=_raise_constant)


class TestSanitizer:
    def test_poisoned_payload_round_trip_is_strict(self):
        from portfolio_engine.app.report_json import sanitize_json_payload

        payload = {
            "matrix": np.array([[1.0, 2.0], [3.0, 4.0]]),
            "int_scalar": np.int64(7),
            "float32_scalar": np.float32(0.5),
            "float_scalar": np.float64(1.25),
            "nan": np.float64(math.nan),
            "inf": np.float64(math.inf),
            "neg_inf": float("-inf"),
            "bool_scalar": np.bool_(True),
            "path": Path("reports/technical-report.json"),
            "a_date": date(2026, 9, 9),
            "a_datetime": datetime(2026, 9, 9, 12, 30, tzinfo=timezone.utc),
            "tuple": (1.0, 2.0),
            "nested": {"list": [np.float64(1.0), None]},
        }
        sanitized = sanitize_json_payload(payload)
        text = json.dumps(sanitized, allow_nan=False, sort_keys=True)
        round_tripped = _strict_loads(text)

        assert round_tripped["matrix"] == [[1.0, 2.0], [3.0, 4.0]]
        assert round_tripped["int_scalar"] == 7
        assert round_tripped["float32_scalar"] == pytest.approx(0.5)
        assert round_tripped["float_scalar"] == 1.25
        assert round_tripped["nan"] is None
        assert round_tripped["inf"] is None
        assert round_tripped["neg_inf"] is None
        assert round_tripped["bool_scalar"] is True
        assert round_tripped["path"] == "reports/technical-report.json"
        assert round_tripped["a_date"] == "2026-09-09"
        assert round_tripped["a_datetime"] == "2026-09-09T12:30:00+00:00"
        assert round_tripped["tuple"] == [1.0, 2.0]
        assert round_tripped["nested"]["list"] == [1.0, None]

    def test_nan_becomes_none_not_zero(self):
        from portfolio_engine.app.report_json import sanitize_json_payload

        sanitized = sanitize_json_payload({"sharpe": float("nan"), "zero": 0.0})
        assert sanitized["sharpe"] is None
        assert sanitized["zero"] == 0.0

    def test_nested_containers_recursed(self):
        from portfolio_engine.app.report_json import sanitize_json_payload

        payload = {"a": [np.array([1, 2]), {"b": (np.float64(2.0),)}]}
        sanitized = sanitize_json_payload(payload)
        assert sanitized == {"a": [[1, 2], {"b": [2.0]}]}


class TestWriter:
    def test_single_file_overwrite_creates_dir(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        target = tmp_path / "reports" / "technical-report.json"
        dump_technical_report({"schema_version": 1, "value": np.float64(1.5)}, target)
        dump_technical_report({"schema_version": 1, "value": 2.5}, target)

        files = list((tmp_path / "reports").iterdir())
        assert files == [target]
        loaded = _strict_loads(target.read_text(encoding="utf-8"))
        assert loaded == {"schema_version": 1, "value": 2.5}

    def test_writer_output_is_strict_parseable(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        target = tmp_path / "out.json"
        dump_technical_report({"bad": float("nan"), "ok": np.float64(2.0)}, target)
        loaded = _strict_loads(target.read_text(encoding="utf-8"))
        assert loaded == {"bad": None, "ok": 2.0}

    def test_writer_overwrites_previous_content(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        target = tmp_path / "over.json"
        dump_technical_report({"v": 1}, target)
        dump_technical_report({"v": 2}, target)
        assert _strict_loads(target.read_text(encoding="utf-8")) == {"v": 2}


class TestFingerprint:
    def test_same_config_same_fingerprint(self):
        from portfolio_engine.app.report_json import config_fingerprint
        from portfolio_engine.core.config import PortfolioConfig

        cfg = PortfolioConfig()
        first = config_fingerprint(cfg, ["AAA", "BBB"], "2021-01-01", "2026-01-01")
        second = config_fingerprint(cfg, ["AAA", "BBB"], "2021-01-01", "2026-01-01")
        assert first == second
        assert len(first) == 16
        int(first, 16)  # hex-decodable

    def test_universe_order_does_not_matter(self):
        from portfolio_engine.app.report_json import config_fingerprint
        from portfolio_engine.core.config import PortfolioConfig

        cfg = PortfolioConfig()
        a = config_fingerprint(cfg, ["AAA", "BBB"], "2021-01-01", "2026-01-01")
        b = config_fingerprint(cfg, ["bbb", "aaa"], "2021-01-01", "2026-01-01")
        assert a == b

    def test_any_config_field_change_moves_fingerprint(self):
        from portfolio_engine.app.report_json import config_fingerprint
        from portfolio_engine.core.config import PortfolioConfig

        base = config_fingerprint(PortfolioConfig(), ["A"], "2021-01-01", "2026-01-01")
        for replaced in [
            dataclasses.replace(PortfolioConfig(), minimum_sharpe_threshold=0.4),
            dataclasses.replace(PortfolioConfig(), maximum_volatility_threshold=0.3),
            dataclasses.replace(PortfolioConfig(), weight_allocation_method="equal"),
            dataclasses.replace(PortfolioConfig(), covariance_estimator="ledoit_wolf"),
            dataclasses.replace(PortfolioConfig(), linkage_method="ward"),
            dataclasses.replace(PortfolioConfig(), risk_free_rate=0.05),
        ]:
            assert config_fingerprint(replaced, ["A"], "2021-01-01", "2026-01-01") != base

    def test_run_id_derived_from_fingerprint_deterministic(self):
        from portfolio_engine.app.report_json import build_report_envelope
        from portfolio_engine.core.config import PortfolioConfig

        cfg = PortfolioConfig()
        args = (["AAA"], cfg, "2021-01-01", "2026-01-01")
        first = build_report_envelope(*args, generated_at="2026-09-09T00:00:00+00:00")
        second = build_report_envelope(*args, generated_at="2026-09-09T00:00:00+00:00")
        assert first["run_id"] == second["run_id"]
        uuid_like = len(first["run_id"]) != 16
        assert not uuid_like


class TestFilterRejections:
    """feat-044 contract: per-ticker filter funnel with threshold distances."""

    METRICS = {
        "GOOD": {"sharpe_ratio": 0.80, "annual_volatility": 0.20},
        "EDGE": {"sharpe_ratio": 0.28, "annual_volatility": 0.20},
        "VOLBAD": {"sharpe_ratio": 0.80, "annual_volatility": 0.35},
        "NANSHARPE": {"sharpe_ratio": float("nan"), "annual_volatility": 0.0},
        "NANVOL": {"sharpe_ratio": 0.80, "annual_volatility": float("inf")},
        "OVERLAP": {"sharpe_ratio": 0.90, "annual_volatility": 0.15},
        "PRUNED": {"sharpe_ratio": 0.70, "annual_volatility": 0.18},
        "ATBOUND": {"sharpe_ratio": 0.3, "annual_volatility": 0.27},
        "DOUBLEBAD": {"sharpe_ratio": 0.10, "annual_volatility": 0.35},
        "DOUBLENAN": {"sharpe_ratio": float("nan"), "annual_volatility": float("inf")},
        "NOPRICE": {"sharpe_ratio": 0.05, "annual_volatility": 0.20},
    }

    def _classify(self):
        from portfolio_engine.app.report_json import compute_filter_rejections
        from portfolio_engine.core.config import PortfolioConfig

        requested = ["GOOD", "EDGE", "VOLBAD", "NANSHARPE", "NANVOL", "OVERLAP",
                     "PRUNED", "ATBOUND", "DOUBLEBAD", "DOUBLENAN", "PHANTOM", "NOPRICE", "GHOST"]
        prices = {t: np.array([100.0]) for t in self.METRICS if t != "NOPRICE"}
        prices["PHANTOM"] = np.array([100.0])  # in bundle, never ingested
        return compute_filter_rejections(
            requested_tickers=requested,
            asset_metrics=self.METRICS,
            filtered_metrics={
                "GOOD": self.METRICS["GOOD"],
                "OVERLAP": self.METRICS["OVERLAP"],
                "ATBOUND": self.METRICS["ATBOUND"],
            },
            closing_prices=prices,
            config=PortfolioConfig(),
        )

    def test_below_min_sharpe_distance_exact(self):
        report = self._classify()
        entry = report["tickers"]["EDGE"]
        assert entry["reason"] == "below_min_sharpe"
        assert entry["d_sharpe"] == pytest.approx(-0.02)
        assert entry["d_vol"] == pytest.approx(0.07)

    def test_above_max_vol_distance_exact(self):
        report = self._classify()
        entry = report["tickers"]["VOLBAD"]
        assert entry["reason"] == "above_max_vol"
        assert entry["d_vol"] == pytest.approx(-0.08)
        assert entry["d_sharpe"] == pytest.approx(0.50)

    def test_non_finite_metrics_get_null_distances(self):
        report = self._classify()
        assert report["tickers"]["NANSHARPE"] == {
            "reason": "sharpe_non_finite", "d_sharpe": None, "d_vol": None,
        }
        assert report["tickers"]["NANVOL"] == {
            "reason": "vol_non_finite", "d_sharpe": None, "d_vol": None,
        }

    def test_ingestion_rejected_for_missing_metrics(self):
        report = self._classify()
        entry = report["tickers"]["GHOST"]
        assert entry["reason"] == "ingestion_rejected"
        assert entry["d_sharpe"] is None and entry["d_vol"] is None

    def test_ingestion_guard_fires_on_either_missing_map(self):
        """Kills or->and and price-half deletion mutants: PHANTOM has prices
        but no metrics; NOPRICE has metrics but no price row."""
        report = self._classify()
        for ticker in ("PHANTOM", "NOPRICE"):
            entry = report["tickers"][ticker]
            assert entry["reason"] == "ingestion_rejected", ticker
            assert entry["d_sharpe"] is None and entry["d_vol"] is None, ticker

    def test_overlap_pruned_when_passing_but_absent_from_filtered(self):
        report = self._classify()
        entry = report["tickers"]["PRUNED"]
        assert entry["reason"] == "overlap_pruned"
        assert entry["d_sharpe"] == pytest.approx(0.40)
        assert entry["d_vol"] == pytest.approx(0.09)

    def test_kept_survivors_have_positive_distances(self):
        report = self._classify()
        entry = report["tickers"]["GOOD"]
        assert entry["reason"] == "kept"
        assert entry["d_sharpe"] == pytest.approx(0.50)
        assert entry["d_vol"] == pytest.approx(0.07)

    def test_sharpe_gate_fires_before_vol_gate(self):
        """Kills below_min<->above_max swap: DOUBLEBAD fails BOTH gates and
        production (selection.py:58-62) classifies by the sharpe gate first."""
        report = self._classify()
        entry = report["tickers"]["DOUBLEBAD"]
        assert entry["reason"] == "below_min_sharpe"
        assert entry["d_sharpe"] == pytest.approx(-0.20)
        assert entry["d_vol"] == pytest.approx(-0.08)

    def test_non_finite_gate_fires_before_vol_gate(self):
        """Kills sharpe_non_finite<->vol_non_finite swap: DOUBLENAN fails both
        non-finite gates and production classifies by the sharpe gate first."""
        report = self._classify()
        assert report["tickers"]["DOUBLENAN"] == {
            "reason": "sharpe_non_finite", "d_sharpe": None, "d_vol": None,
        }

    def test_exact_threshold_boundary_passes(self):
        """Kills < -> <= and > -> >= mutants: at sharpe==min and vol==max the
        production filter (selection.py:58,61 strict) KEEPS the asset."""
        report = self._classify()
        entry = report["tickers"]["ATBOUND"]
        assert entry["reason"] == "kept"
        assert entry["d_sharpe"] == pytest.approx(0.0, abs=0.0)
        assert entry["d_vol"] == pytest.approx(0.0, abs=0.0)

    def test_empty_requested_universe(self):
        from portfolio_engine.app.report_json import compute_filter_rejections
        from portfolio_engine.core.config import PortfolioConfig

        report = compute_filter_rejections(
            requested_tickers=[],
            asset_metrics=self.METRICS,
            filtered_metrics={"GOOD": self.METRICS["GOOD"]},
            closing_prices={"GOOD": np.array([100.0])},
            config=PortfolioConfig(),
        )
        assert report["tickers"] == {}
        assert report["counts"] == {"requested": 0, "kept": 0, "rejected": 0}

    def test_duplicate_requested_tickers_dedupe(self):
        from portfolio_engine.app.report_json import compute_filter_rejections
        from portfolio_engine.core.config import PortfolioConfig

        report = compute_filter_rejections(
            requested_tickers=["GOOD", "GOOD", "EDGE"],
            asset_metrics=self.METRICS,
            filtered_metrics={"GOOD": self.METRICS["GOOD"]},
            closing_prices={"GOOD": np.array([100.0])},
            config=PortfolioConfig(),
        )
        assert report["counts"] == {"requested": 2, "kept": 1, "rejected": 1}
        assert len(report["tickers"]) == 2

    def test_thresholds_and_counts_consistent(self):
        report = self._classify()
        assert report["thresholds"] == {"min_sharpe": 0.3, "max_volatility": 0.27}
        counts = report["counts"]
        assert counts == {"requested": 13, "kept": 3, "rejected": 10}
        assert counts["kept"] + counts["rejected"] == counts["requested"]
        assert set(report["tickers"]) == {
            "GOOD", "EDGE", "VOLBAD", "NANSHARPE", "NANVOL", "OVERLAP",
            "PRUNED", "ATBOUND", "DOUBLEBAD", "DOUBLENAN", "PHANTOM", "NOPRICE", "GHOST",
        }

    def test_derived_reasons_match_production_filter(self):
        """Reason parity vs production: every classification the report derives
        must be derivable from the SAME guard order apply_asset_filters uses
        (non-finite -> sharpe -> vol), plus the calendar-prune layer that the
        final filtered set encodes. NOPRICE is excluded upstream (missing price
        row), so production never reaches it; the report labels it
        ingestion_rejected instead."""
        from portfolio_engine.portfolio.selection import apply_asset_filters

        production_prices = {t: np.array([100.0]) for t in self.METRICS if t != "NOPRICE"}
        production_filtered, _ = apply_asset_filters(
            {t: dict(m) for t, m in self.METRICS.items() if t != "NOPRICE"},
            production_prices,
            0.3,
            0.27,
        )
        assert set(production_filtered) == {"GOOD", "OVERLAP", "PRUNED", "ATBOUND"}
        report = self._classify()
        classify_filtered = {"GOOD", "OVERLAP", "ATBOUND"}
        for ticker, metrics in self.METRICS.items():
            if ticker not in production_prices:
                expected = "ingestion_rejected"
            elif not np.isfinite(metrics["sharpe_ratio"]):
                expected = "sharpe_non_finite"
            elif not np.isfinite(metrics["annual_volatility"]):
                expected = "vol_non_finite"
            elif metrics["sharpe_ratio"] < 0.3:
                expected = "below_min_sharpe"
            elif metrics["annual_volatility"] > 0.27:
                expected = "above_max_vol"
            elif ticker in classify_filtered:
                expected = "kept"
            else:
                expected = "overlap_pruned"
            assert report["tickers"][ticker]["reason"] == expected, ticker

    def test_reasons_survive_strict_json_serialization(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        target = tmp_path / "r.json"
        dump_technical_report({"filtering": self._classify()}, target)
        loaded = _strict_loads(target.read_text(encoding="utf-8"))
        assert loaded["filtering"]["counts"]["kept"] == 3
        assert loaded["filtering"]["tickers"]["NANSHARPE"]["d_sharpe"] is None


class TestAllocationDiagnostics:
    """feat-045 contract: concentration, diversification and Dykstra telemetry."""

    @staticmethod
    def _pd_cov(spread=(0.04, 0.01)):
        """Deterministic 2-block PD covariance via seeded rng."""
        rng = np.random.default_rng(11)
        n = 4
        raw = rng.normal(scale=0.01, size=(n, n))
        cov = raw @ raw.T + np.diag(spread[0] * np.ones(n) / n + spread[1] * np.ones(n) * 0.0)
        return cov + np.eye(n) * 0.01

    def _diag(self, weights, cov, cov_tickers, config=None, raw_weights=None):
        from portfolio_engine.app.report_json import allocation_diagnostics
        from portfolio_engine.core.config import PortfolioConfig

        return allocation_diagnostics(
            weights, cov, cov_tickers, config or PortfolioConfig(), raw_weights=raw_weights,
        )

    def test_equal_weights_four_assets_hhi(self):
        cov = self._pd_cov()
        report = self._diag({t: 0.25 for t in ("A", "B", "C", "D")}, cov, ["A", "B", "C", "D"])
        assert report["method"] == "hrp"
        assert report["hhi"] == pytest.approx(0.25)
        assert report["n_effective"] == pytest.approx(4.0)
        assert report["n_assets"] == 4

    def test_single_asset_identity(self):
        report = self._diag({"T": 1.0}, np.array([[0.04]]), ["T"])
        assert report["hhi"] == pytest.approx(1.0)
        assert report["n_effective"] == pytest.approx(1.0)
        assert report["diversification_ratio"] == pytest.approx(1.0)
        assert report["risk_contributions"] == {"T": pytest.approx(1.0)}
        assert report["raw_vs_constrained"]["mandate_relaxed"] is True  # n=1 relaxes max
        assert report["raw_vs_constrained"]["effective_bounds"]["max"] == pytest.approx(1.0)

    def test_empty_universe_all_none(self):
        report = self._diag({}, np.empty((0, 0)), [])
        assert report["n_assets"] == 0
        assert report["hhi"] is None
        assert report["n_effective"] is None
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None
        assert report["rc_spread"] is None
        assert report["raw_vs_constrained"] is None

    def test_weight_sum_violation_named_error(self):
        from portfolio_engine.core.config import PortfolioConfig

        with pytest.raises(ValueError, match="sum to 1"):
            self._diag({"A": 0.6, "B": 0.6}, np.eye(2) * 0.04, ["A", "B"], PortfolioConfig())

    def test_non_finite_weight_yields_nan_hhi_and_null_risk(self):
        report = self._diag({"A": float("nan"), "B": 0.5}, np.eye(2) * 0.04, ["A", "B"])
        assert math.isnan(report["hhi"])
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None

    def test_covariance_slice_legacy_m_n_matches_direct(self):
        rng = np.random.default_rng(5)
        base = rng.normal(scale=0.01, size=(5, 5))
        full = base @ base.T + np.eye(5) * 0.02
        full_tickers = ["A", "B", "C", "D", "E"]
        weights = {"B": 0.5, "E": 0.3, "A": 0.2}
        report = self._diag(weights, full, full_tickers)
        # Direct computation over the extracted 3x3 submatrix:
        direct_cov = full[np.ix_([1, 4, 0], [1, 4, 0])]
        direct_w = np.array([0.5, 0.3, 0.2])
        direct_dr = (direct_w @ np.sqrt(np.diag(direct_cov))) / np.sqrt(direct_w @ direct_cov @ direct_w)
        assert report["diversification_ratio"] == pytest.approx(direct_dr, rel=1e-12)
        direct_rc = direct_w * (direct_cov @ direct_w) / (direct_w @ direct_cov @ direct_w)
        assert list(report["risk_contributions"].values()) == pytest.approx(list(direct_rc), rel=1e-12)
        assert sum(report["risk_contributions"].values()) == pytest.approx(1.0, abs=1e-9)
        assert list(report["risk_contributions"]) == ["B", "E", "A"]

    def test_order_invariance_permuted_weights(self):
        cov = self._pd_cov()
        tickers = ["A", "B", "C", "D"]
        base = self._diag(dict(zip(tickers, [0.25] * 4)), cov, tickers)
        permuted = self._diag(dict(zip(reversed(tickers), [0.25] * 4)), cov, tickers)
        assert permuted["hhi"] == pytest.approx(base["hhi"])
        assert permuted["diversification_ratio"] == pytest.approx(base["diversification_ratio"], rel=1e-12)
        assert list(permuted["risk_contributions"]) == list(reversed(tickers))

    def test_risk_contributions_sum_one_seeded(self):
        rng = np.random.default_rng(9)
        cov = rng.normal(scale=0.01, size=(4, 4)) @ rng.normal(scale=0.01, size=(4, 4)).T + np.eye(4) * 0.03
        report = self._diag({t: 0.25 for t in ("A", "B", "C", "D")}, cov, ["A", "B", "C", "D"])
        assert sum(report["risk_contributions"].values()) == pytest.approx(1.0, abs=1e-9)
        spread = report["rc_spread"]
        assert spread["std"] >= 0.0
        assert spread["max_over_equal"] >= 1.0
        assert spread["max_minus_min"] == pytest.approx(
            max(report["risk_contributions"].values()) - min(report["risk_contributions"].values())
        )

    def test_raw_weights_provided_compute_l1_any_method(self):
        from dataclasses import replace

        from portfolio_engine.core.config import PortfolioConfig

        cfg = replace(PortfolioConfig(), weight_allocation_method="equal")
        report = self._diag(
            {"A": 0.4, "B": 0.6}, np.eye(2) * 0.04, ["A", "B"], cfg,
            raw_weights=np.array([0.5, 0.5]),
        )
        rvc = report["raw_vs_constrained"]
        assert rvc["l1_raw_to_constrained"] == pytest.approx(0.2)
        assert rvc["max_weight_drop"] == pytest.approx(0.1)
        assert rvc["n_weights_changed"] == 2
        assert rvc["mandate_relaxed"] is True  # n=2 always relaxes (2*0.30 < 1)
        assert rvc["effective_bounds"]["max"] == pytest.approx(0.5)

    def test_hrp_recompute_bit_identical_when_bounds_dont_bite(self):
        """Equal diagonal variance -> HRP bisection yields exactly 1/N; the
        recompute must match the engine bit-for-bit so l1 == 0 and the
        constrained vector equals the raw one (Dykstra no-op at n=4)."""
        cov = np.diag([0.04, 0.04, 0.04, 0.04])
        report = self._diag({t: 0.25 for t in ("A", "B", "C", "D")}, cov, ["A", "B", "C", "D"])
        rvc = report["raw_vs_constrained"]
        assert rvc["l1_raw_to_constrained"] == pytest.approx(0.0, abs=1e-12)
        assert rvc["n_weights_changed"] == 0
        assert rvc["mandate_relaxed"] is False

    def test_hrp_recompute_exposes_dystra_drift_when_cap_bites(self):
        """diag(0.01,0.04): raw HRP = [0.8,0.2] analytically; n=2 relaxes max to
        0.5, Dykstra caps A -> constrained [0.5,0.5]; the recomputed raw must
        equal the analytic vector, exposing the flattening telemetry."""
        cov = np.diag([0.01, 0.04])
        report = self._diag({"A": 0.5, "B": 0.5}, cov, ["A", "B"])
        rvc = report["raw_vs_constrained"]
        assert rvc["l1_raw_to_constrained"] == pytest.approx(0.6)
        assert rvc["max_weight_drop"] == pytest.approx(0.3)
        assert rvc["n_weights_changed"] == 2
        assert rvc["mandate_relaxed"] is True
        assert rvc["effective_bounds"]["max"] == pytest.approx(0.5)

    def test_degenerate_covariance_null_risk_but_hhi_stands(self):
        report = self._diag({t: 0.25 for t in ("A", "B", "C", "D")}, np.zeros((4, 4)), ["A", "B", "C", "D"])
        assert report["hhi"] == pytest.approx(0.25)
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None
        assert report["rc_spread"] is None
        assert report["raw_vs_constrained"] is None  # engine rejects zeros; no recompute

    def test_engine_round_trip_bit_identity_patched_panel(self, patched_batch):
        """MAJOR-2 pin (a): drive the REAL engine route (ingesta -> filtros ->
        alineacion -> covarianza -> calculate_optimal_portfolio_weights_hrp)
        over the conftest synthetic panel, then feed its weights + covariance
        into the diagnostics recompute. Same deterministic inputs -> l1 == 0
        when Dykstra does not bite (4 similar-vol assets -> ~1/N weights)."""
        from portfolio_engine.core.config import PortfolioConfig
        from portfolio_engine.core.metrics import (
            align_prices_to_common_calendar,
            construct_returns_matrix,
            estimate_covariance,
        )
        from portfolio_engine.data.data_fetch import download_and_calculate_metrics
        from portfolio_engine.portfolio.allocation import calculate_optimal_portfolio_weights_hrp
        from portfolio_engine.portfolio.selection import apply_asset_filters

        cfg = PortfolioConfig()
        tickers = ["E1", "E2", "E3", "E4"]
        patched_batch({t: {} for t in tickers}, rows=300)
        metrics, prices, dates = download_and_calculate_metrics(
            tickers, cfg.risk_free_rate, cfg.lookback_years, cfg.trading_days_per_year
        )
        filtered_metrics, filtered_prices = apply_asset_filters(
            metrics, prices, cfg.minimum_sharpe_threshold, cfg.maximum_volatility_threshold
        )
        aligned = align_prices_to_common_calendar(filtered_prices, dates, cfg.minimum_overlap_ratio)
        returns_matrix = construct_returns_matrix(aligned)
        cov = estimate_covariance(returns_matrix, cfg.covariance_estimator)
        engine_weights = calculate_optimal_portfolio_weights_hrp(filtered_metrics, cov, cfg)

        # 3 survivors -> mandate relaxed to 1/3 (Dykstra bit); the diagnostics
        # recompute must be BIT-IDENTICAL to the engine's own raw vector, so its
        # reported l1 equals the independently computed Dykstra distance:
        assert len(engine_weights) == 3
        report = self._diag(engine_weights, cov, list(filtered_metrics.keys()), cfg)
        rvc = report["raw_vs_constrained"]
        assert rvc is not None
        assert rvc["mandate_relaxed"] is True
        assert rvc["effective_bounds"]["max"] == pytest.approx(1 / 3)
        from portfolio_engine.portfolio.hrp import calculate_hrp_weights

        independent_raw = calculate_hrp_weights(cov, linkage_method=cfg.linkage_method)
        engine_order = list(filtered_metrics.keys())
        independent_l1 = float(np.abs(independent_raw - np.array([engine_weights[t] for t in engine_order])).sum())
        assert rvc["l1_raw_to_constrained"] == pytest.approx(independent_l1, abs=1e-15)
        assert rvc["l1_raw_to_constrained"] > 0.0  # the cap bit
        assert rvc["max_weight_drop"] == pytest.approx(
            float(max(independent_raw - np.array([engine_weights[t] for t in engine_order]))), abs=1e-15
        )

    def test_three_assets_mandate_relaxed_pin(self):
        """MAJOR-2 pin (b): n=3 with max=0.30 is mathematically infeasible
        (3*0.30 < 1) -> effective max becomes 1/3 with mandate_relaxed True."""
        report = self._diag(
            {t: 1 / 3 for t in ("A", "B", "C")}, np.eye(3) * 0.04, ["A", "B", "C"]
        )
        rvc = report["raw_vs_constrained"]
        assert rvc["mandate_relaxed"] is True
        assert rvc["effective_bounds"]["max"] == pytest.approx(1 / 3)
        assert rvc["effective_bounds"]["min"] == pytest.approx(0.05)

    def test_negative_weights_named_error(self):
        with pytest.raises(ValueError, match="Long-only mandate"):
            self._diag({"A": 2.0, "B": -1.0}, np.eye(2) * 0.04, ["A", "B"])

    def test_raw_weights_shape_mismatch_named_error(self):
        with pytest.raises(ValueError, match="raw_weights shape"):
            self._diag(
                {"A": 0.5, "B": 0.5}, np.eye(2) * 0.04, ["A", "B"],
                raw_weights=np.array([0.4, 0.4, 0.2]),
            )

    def test_nan_raw_weights_null_telemetry(self):
        report = self._diag(
            {"A": 0.5, "B": 0.5}, np.eye(2) * 0.04, ["A", "B"],
            raw_weights=np.array([float("nan"), 0.5]),
        )
        assert report["raw_vs_constrained"] is None

    def test_sub_threshold_diff_not_counted_as_changed(self):
        """MINOR-3: diffs below 1e-12 are rounding noise, never 'changed' —
        kills the 1e-12 -> 0.0 threshold mutant."""
        report = self._diag(
            {t: 0.25 for t in ("A", "B", "C", "D")}, np.diag([0.04] * 4), ["A", "B", "C", "D"],
            raw_weights=np.array([0.25 + 1e-13, 0.25 - 1e-13, 0.25, 0.25]),
        )
        rvc = report["raw_vs_constrained"]
        assert rvc["n_weights_changed"] == 0
        assert rvc["l1_raw_to_constrained"] > 0.0

    def test_max_over_equal_pinned_exactly(self):
        report = self._diag({t: 0.25 for t in ("A", "B", "C", "D")}, self._pd_cov(), ["A", "B", "C", "D"])
        rc = report["risk_contributions"]
        assert report["rc_spread"]["max_over_equal"] == pytest.approx(max(rc.values()) * 4)

    def test_covariance_ticker_count_mismatch_named(self):
        with pytest.raises(ValueError, match="must match"):
            self._diag({"A": 0.5, "B": 0.5}, np.eye(2) * 0.04, ["A", "B", "C"])

    def test_non_hrp_method_raw_vs_constrained_null(self):
        from dataclasses import replace

        from portfolio_engine.core.config import PortfolioConfig

        cfg = replace(PortfolioConfig(), weight_allocation_method="risk_parity")
        report = self._diag({"A": 0.5, "B": 0.5}, np.eye(2) * 0.04, ["A", "B"], cfg)
        assert report["method"] == "risk_parity"
        assert report["raw_vs_constrained"] is None

    def test_missing_weight_ticker_raises_named(self):
        with pytest.raises(ValueError, match="not in covariance"):
            self._diag({"Z": 1.0}, np.eye(1) * 0.04, ["A"])

    def test_section_survives_strict_json_serialization(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        target = tmp_path / "r.json"
        report = self._diag({"A": float("nan"), "B": 1.0}, np.eye(2) * 0.04, ["A", "B"])
        dump_technical_report({"allocation": report}, target)
        loaded = _strict_loads(target.read_text(encoding="utf-8"))
        assert loaded["allocation"]["hhi"] is None
        assert loaded["allocation"]["diversification_ratio"] is None

    def test_hrp_legacy_m_n_telemetry_null_no_fabrication(self):
        """Hardening F1: HRP method with a full-universe N×N covariance but
        subset weights (M<N) yields raw_vs_constrained None — a recompute on
        the slice would not be the engine's raw vector. DR/RC still served."""
        rng = np.random.default_rng(5)
        base = rng.normal(scale=0.01, size=(5, 5))
        full = base @ base.T + np.eye(5) * 0.02
        report = self._diag({"B": 0.5, "E": 0.3, "A": 0.2}, full, ["A", "B", "C", "D", "E"])
        assert report["method"] == "hrp"
        assert report["raw_vs_constrained"] is None
        assert report["diversification_ratio"] is not None
        assert sum(report["risk_contributions"].values()) == pytest.approx(1.0, abs=1e-9)

    def test_permuted_unequal_weights_joint_permutation_consistent(self):
        """Hardening F2: joint permutation (weights + tickers + covariance +
        raw) preserves HHI/DR/RC/l1 — internal alignment, not luck of equal
        weights. Engine bit-identity still needs pipeline order (docstring)."""
        tickers = ["A", "B", "C", "D"]
        wvals = [0.4, 0.3, 0.2, 0.1]
        raw = [0.35, 0.3, 0.2, 0.15]
        cov = self._pd_cov()
        base = self._diag(
            dict(zip(tickers, wvals)), cov, tickers, raw_weights=np.array(raw)
        )
        perm = [3, 2, 1, 0]
        ptickers = [tickers[i] for i in perm]
        moved = self._diag(
            dict(zip(ptickers, [wvals[i] for i in perm])),
            cov[np.ix_(perm, perm)],
            ptickers,
            raw_weights=np.array([raw[i] for i in perm]),
        )
        assert moved["hhi"] == pytest.approx(base["hhi"])
        assert moved["diversification_ratio"] == pytest.approx(
            base["diversification_ratio"], rel=1e-12
        )
        assert moved["raw_vs_constrained"]["l1_raw_to_constrained"] == pytest.approx(
            base["raw_vs_constrained"]["l1_raw_to_constrained"], rel=1e-12
        )
        assert moved["risk_contributions"] == {
            t: pytest.approx(base["risk_contributions"][t]) for t in ptickers
        }

    def test_indefinite_covariance_null_risk_without_warning(self):
        """Hardening F4: correlation-impossible slice (negative wᵀΣw) → risk
        None, never inf, and no RuntimeWarning leaks (variance is guarded
        pre-sqrt). HHI stands: concentration needs no covariance."""
        import warnings
        from dataclasses import replace

        from portfolio_engine.core.config import PortfolioConfig

        cfg = replace(PortfolioConfig(), weight_allocation_method="equal")
        bad = np.array([[0.04, -0.05], [-0.05, 0.04]])  # corr -1.25, invalid
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            report = self._diag({"A": 0.5, "B": 0.5}, bad, ["A", "B"], cfg)
        assert report["hhi"] == pytest.approx(0.5)
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None
        assert report["rc_spread"] is None

    def test_inf_covariance_null_risk(self):
        """Pins the isfinite conjunct: +inf variance is not > floor material —
        risk stays None instead of leaking inf into the report."""
        from dataclasses import replace

        from portfolio_engine.core.config import PortfolioConfig

        cfg = replace(PortfolioConfig(), weight_allocation_method="equal")
        inf_cov = np.array([[float("inf"), 0.0], [0.0, 0.04]])
        report = self._diag({"A": 0.5, "B": 0.5}, inf_cov, ["A", "B"], cfg)
        assert report["hhi"] == pytest.approx(0.5)
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None
        assert report["rc_spread"] is None

    def test_hrp_legacy_m_n_with_caller_raw_reports_telemetry(self):
        """Companion to the F1 null pin: the None branch is about missing
        raw truth, not about M<N — caller-supplied raw_weights are reported
        verbatim even on the legacy slice (no fabrication: caller truth)."""
        report = self._diag(
            {"B": 0.5, "E": 0.3, "A": 0.2},
            np.diag([0.04, 0.04, 0.04, 0.04, 0.04]),
            ["A", "B", "C", "D", "E"],
            raw_weights=np.array([0.4, 0.3, 0.3]),
        )
        rvc = report["raw_vs_constrained"]
        assert rvc is not None
        assert rvc["l1_raw_to_constrained"] == pytest.approx(0.2)
        assert rvc["n_weights_changed"] == 2
        assert report["diversification_ratio"] is not None  # slice still served

    def test_nan_covariance_null_risk(self):
        """Hardening F4: NaN covariance → risk sections None (guarded by the
        finite-variance check), HHI untouched."""
        from dataclasses import replace

        from portfolio_engine.core.config import PortfolioConfig

        cfg = replace(PortfolioConfig(), weight_allocation_method="equal")
        nan_cov = np.array([[0.04, float("nan")], [float("nan"), 0.04]])
        report = self._diag({"A": 0.5, "B": 0.5}, nan_cov, ["A", "B"], cfg)
        assert report["hhi"] == pytest.approx(0.5)
        assert report["diversification_ratio"] is None
        assert report["risk_contributions"] is None

    def test_duplicate_covariance_tickers_raise_named(self):
        """Hardening F3: duplicated covariance rows fail loud — silent
        first-occurrence binding would mask ticker misalignment."""
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            self._diag({"A": 0.5, "B": 0.5}, np.eye(3) * 0.04, ["A", "A", "B"])

    def test_raw_weights_list_accepted_and_2d_rejected(self):
        """Hardening F5: list raw_weights work via asarray; 2-D (n,1) hits
        the named shape error instead of broadcasting silently."""
        listed = self._diag(
            {"A": 0.4, "B": 0.6}, np.eye(2) * 0.04, ["A", "B"],
            raw_weights=[0.5, 0.5],
        )
        assert listed["raw_vs_constrained"]["l1_raw_to_constrained"] == pytest.approx(0.2)
        with pytest.raises(ValueError, match="raw_weights shape"):
            self._diag(
                {"A": 0.5, "B": 0.5}, np.eye(2) * 0.04, ["A", "B"],
                raw_weights=np.array([[0.5], [0.5]]),
            )

    def test_empty_weights_non_empty_covariance_all_none(self):
        """Hardening F5: N=0 short-circuits before every guard — the empty
        universe reports null sections however much covariance is passed."""
        report = self._diag({}, np.eye(2) * 0.04, ["A", "B"])
        assert report["n_assets"] == 0
        assert report["hhi"] is None
        assert report["diversification_ratio"] is None
        assert report["raw_vs_constrained"] is None

    def test_non_finite_weight_nan_effective_and_long_only_dr_floor(self):
        """Hardening F6/F7 + external #1/#2: n_effective is NaN (not just
        hhi) on non-finite weights; long-only DR respects the Choueifaty
        floor DR ≥ 1; ΣRC == 1 within 1e-8; rc_spread std is population
        (ddof=0) by explicit convention."""
        report = self._diag({"A": float("nan"), "B": 0.5}, np.eye(2) * 0.04, ["A", "B"])
        assert math.isnan(report["n_effective"])
        sane = self._diag(
            {t: 0.25 for t in ("A", "B", "C", "D")}, self._pd_cov(), ["A", "B", "C", "D"]
        )
        assert sane["diversification_ratio"] >= 1.0
        assert sum(sane["risk_contributions"].values()) == pytest.approx(1.0, abs=1e-8)
        assert sane["rc_spread"]["std"] == pytest.approx(
            float(np.std(np.array(list(sane["risk_contributions"].values())), ddof=0))
        )

    def test_export_surface_allocation_diagnostics(self):
        import portfolio_engine.app as app

        assert hasattr(app, "allocation_diagnostics")


class TestInsampleTailDrawdown:
    """feat-046 contract: in-sample series, tail risk, drawdown (TDD red-first)."""

    @staticmethod
    def _tail(series, rf=0.045, trading_days=252):
        from portfolio_engine.app.report_json import tail_risk_metrics

        return tail_risk_metrics(series, rf, trading_days)

    @staticmethod
    def _dd(series, trading_days=252):
        from portfolio_engine.app.report_json import drawdown_metrics

        return drawdown_metrics(series, trading_days)

    def test_prs_pin_log_diffs_dot_weights(self):
        from portfolio_engine.app.report_json import portfolio_return_series

        prices = {"A": [100.0, 101.0, 102.0], "B": [50.0, 49.0, 49.5]}
        weights = {"A": 0.6, "B": 0.4}
        series = portfolio_return_series(prices, weights)
        assert isinstance(series, np.ndarray)
        ra = np.log(np.array([101.0 / 100.0, 102.0 / 101.0]))
        rb = np.log(np.array([49.0 / 50.0, 49.5 / 49.0]))
        assert series == pytest.approx(0.6 * ra + 0.4 * rb, rel=1e-12)
        assert len(series) == 2  # T prices -> T-1 returns

    def test_prs_key_mismatch_named_error(self):
        from portfolio_engine.app.report_json import portfolio_return_series

        with pytest.raises(ValueError, match="without aligned prices"):
            portfolio_return_series({"A": [1.0, 2.0]}, {"A": 0.5, "Z": 0.5})

    def test_prs_price_without_weight_zero_embedded(self):
        """Asymmetry (legacy M<N): price series without weight are embedded
        at zero — only a WEIGHT without prices is uncomputable (raises)."""
        from portfolio_engine.app.report_json import portfolio_return_series

        series = portfolio_return_series(
            {"A": [100.0, 101.0], "B": [50.0, 51.0]}, {"A": 1.0}
        )
        assert series == pytest.approx(np.log(np.array([101.0 / 100.0])), rel=1e-12)

    def test_prs_legacy_zero_embed(self):
        """M<N: subset weights zero-embedded over the aligned price universe."""
        from portfolio_engine.app.report_json import portfolio_return_series

        prices = {
            "A": [100.0, 101.0, 102.0],
            "B": [50.0, 49.0, 49.5],
            "C": [10.0, 10.5, 10.2],
        }
        series = portfolio_return_series(prices, {"A": 0.7, "C": 0.3})
        ra = np.log(np.array([101.0 / 100.0, 102.0 / 101.0]))
        rc = np.log(np.array([10.5 / 10.0, 10.2 / 10.5]))
        assert series == pytest.approx(0.7 * ra + 0.3 * rc, rel=1e-12)

    def test_prs_realign_regression_ratio_one(self):
        """Re-align contract: ratio=1.0 reproduces the intersection-dropna the
        engine used (no survivor excluded); the series spans common-rows - 1."""
        from portfolio_engine.app.report_json import portfolio_return_series
        from portfolio_engine.core.metrics import align_prices_to_common_calendar

        full_idx = [f"2020-01-0{d}" for d in range(1, 7)]
        prices = {
            # Gappy survivor: interior NaN is droppable, keeps 5 valid rows.
            "KEEP": [100.0, 101.0, float("nan"), 103.0, 104.0, 105.0],
            "FULL": [50.0, 51.0, 52.0, 53.0, 54.0, 55.0],
        }
        aligned = align_prices_to_common_calendar(
            prices, {t: full_idx for t in prices}, 1.0
        )
        assert set(aligned) == {"KEEP", "FULL"}
        n_common = len(next(iter(aligned.values())))
        series = portfolio_return_series(aligned, {"KEEP": 0.5, "FULL": 0.5})
        assert len(series) == n_common - 1

    def test_prs_realign_point_nine_would_exclude_survivor(self):
        """Counterexample leg: an 8/10-coverage survivor is EXCLUDED by the
        0.9 guard but kept by 1.0 — callers must use 1.0 (feat-050 contract)."""
        from portfolio_engine.app.report_json import portfolio_return_series
        from portfolio_engine.core.metrics import align_prices_to_common_calendar

        idx = [f"2020-02-{d:02d}" for d in range(1, 11)]
        prices = {
            "THIN": [100.0 + i for i in range(8)],
            "FULL": [50.0 + i for i in range(10)],
        }
        dates = {"THIN": idx[:8], "FULL": idx}
        pruned = align_prices_to_common_calendar(prices, dates, 0.9)
        assert "THIN" not in pruned
        kept = align_prices_to_common_calendar(prices, dates, 1.0)
        assert set(kept) == {"THIN", "FULL"}
        series = portfolio_return_series(kept, {"THIN": 0.5, "FULL": 0.5})
        assert len(series) == len(next(iter(kept.values()))) - 1

    def test_prs_empty_weights_named_error(self):
        from portfolio_engine.app.report_json import portfolio_return_series

        with pytest.raises(ValueError, match="empty weights"):
            portfolio_return_series({"A": [1.0, 2.0]}, {})

    def test_prs_ragged_lengths_named_error(self):
        from portfolio_engine.app.report_json import portfolio_return_series

        with pytest.raises(ValueError, match="ragged"):
            portfolio_return_series(
                {"A": [1.0, 2.0, 3.0], "B": [1.0, 2.0]}, {"A": 0.5, "B": 0.5}
            )

    def test_prs_no_sum_normalization(self):
        """Leveraged weights are valid series input: no silent renormalization
        (a w/=sum mutant would halve this series)."""
        from portfolio_engine.app.report_json import portfolio_return_series

        prices = {"A": [100.0, 101.0, 102.0], "B": [50.0, 49.0, 49.5]}
        series = portfolio_return_series(prices, {"A": 1.2, "B": 0.8})
        ra = np.log(np.array([101.0 / 100.0, 102.0 / 101.0]))
        rb = np.log(np.array([49.0 / 50.0, 49.5 / 49.0]))
        assert series == pytest.approx(1.2 * ra + 0.8 * rb, rel=1e-12)

    def test_tail_constant_series_rf0045_uses_log_target(self):
        """Analytic pin: constant series c BELOW the daily target,
        rf=0.045 -> numerator uses ln(1.045) and daily target
        ln(1.045)/252, rel 1e-12."""
        c = 0.0001  # below td ~= 0.0001746: every day is a down day
        n = 300
        out = self._tail([c] * n)
        t = math.log1p(0.045)
        td = t / 252
        dd = abs(min(0.0, c - td)) * math.sqrt(252)
        assert out["downside_deviation_annual"] == pytest.approx(dd, rel=1e-12)
        assert out["sortino_ratio"] == pytest.approx((c * 252 - t) / dd, rel=1e-12)
        assert out["target_daily"] == pytest.approx(td, rel=1e-12)
        assert out["n_obs"] == n
        assert out["frequency"] == "daily"
        assert out["sample"] == "in-sample"
        assert out["costs"] == "no-costs"

    def test_tail_len_lt2_none_with_reason(self):
        for serie in ([], [0.01]):
            out = self._tail(serie)
            assert out["sortino_ratio"] is None
            assert out["var_95_daily"] is None
            assert out["cvar_95_daily"] is None
            assert out["reason"]

    def test_tail_nonfinite_all_none(self):
        """Any non-finite observation -> whole section None+reason (no silent
        trimming: dropping points would fabricate a cleaner sample)."""
        out = self._tail([0.01, 0.02, float("nan"), 0.015] * 50)
        assert out["sortino_ratio"] is None
        assert out["var_95_daily"] is None
        assert out["cvar_95_daily"] is None
        assert out["reason"]
        out = self._tail([0.01, float("inf"), 0.02] * 50)
        assert out["sortino_ratio"] is None

    def test_tail_no_downside_sortino_null_var_numeric(self):
        out = self._tail([0.01] * 300)
        assert out["sortino_ratio"] is None
        assert out["downside_deviation_annual"] is None
        assert out["reason"]
        assert out["var_95_daily"] is not None
        assert out["cvar_95_daily"] is not None
        # Signed invariant (always): -mean(tail) >= -q05. The |VaR| form only
        # holds when VaR >= 0 (genuine loss tail); here q05 > 0 by construction.
        assert out["cvar_95_daily"] >= out["var_95_daily"] - 1e-15

    def test_tail_mixed_downside_denominator_over_total_n(self):
        """Kills the down-days-only denominator mutant: with 2 down of 4
        days, total-N mean (0.000125) != down-only mean (0.00025)."""
        serie = [0.01, -0.02, 0.03, -0.01]
        out = self._tail(serie, rf=0.0)
        dd = math.sqrt(0.000125) * math.sqrt(252)
        assert out["downside_deviation_annual"] == pytest.approx(dd, rel=1e-12)
        assert out["sortino_ratio"] == pytest.approx(0.0025 * 252 / dd, rel=1e-12)

    def test_tail_point_mass_inclusive_tail(self):
        """Kills the strict-< mutant: q05 lands exactly on the -0.02 mass;
        inclusive <= keeps all 10 tail points (strict < would empty it)."""
        serie = [0.05] * 10 + [-0.02] * 10
        out = self._tail(serie, rf=0.0)
        assert out["n_tail"] == 10
        assert out["var_95_daily"] == pytest.approx(0.02, rel=1e-12)
        assert out["cvar_95_daily"] == pytest.approx(0.02, rel=1e-12)

    def test_tail_explicit_trading_days_pinned(self):
        """Kills the hardcoded-252 mutant: T=126 re-derives target AND dev."""
        c, n, t_days = 0.0001, 200, 126
        out = self._tail([c] * n, trading_days=t_days)
        target = math.log1p(0.045) / t_days
        dd = abs(c - target) * math.sqrt(t_days)
        assert out["downside_deviation_annual"] == pytest.approx(dd, rel=1e-12)
        assert out["sortino_ratio"] == pytest.approx(
            (c * t_days - math.log1p(0.045)) / dd, rel=1e-12
        )

    def test_tail_nonfinite_risk_free_all_none(self):
        out = self._tail([0.01] * 100, rf=float("nan"))
        assert out["sortino_ratio"] is None
        assert out["var_95_daily"] is None
        assert out["reason"] == "non-finite-risk-free-target"

    def test_trading_days_non_positive_named_error(self):
        from portfolio_engine.app.report_json import drawdown_metrics

        with pytest.raises(ValueError, match="trading_days must be positive"):
            self._tail([0.01] * 100, trading_days=0)
        with pytest.raises(ValueError, match="trading_days must be positive"):
            drawdown_metrics([0.01] * 100, trading_days=-1)

    def test_drawdown_degenerate_none_with_reason(self):
        out = self._dd([0.5])
        assert out["max_drawdown"] is None
        assert out["reason"] == "n_obs<2"
        out = self._dd([0.01, float("nan"), 0.02] * 50)
        assert out["max_drawdown"] is None
        assert out["calmar_ratio"] is None
        assert out["reason"] == "non-finite-observations"

    def test_drawdown_overflow_null_without_warning(self):
        """Pathological compounding (cumsum ~2000): exp overflows — null with
        reason, never nan leakage nor RuntimeWarning."""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            out = self._dd([10.0] * 200)
        assert out["max_drawdown"] is None
        assert out["calmar_ratio"] is None
        assert out["reason"] == "wealth-overflow-non-finite"

    def test_var_cvar_pins_linear_interpolation(self):
        """VaR = -quantile(r, 0.05, method='linear'); CVaR = -mean(r | r<=q05)
        inclusive tail; never sqrt-scaled."""
        rng = np.random.default_rng(7)
        serie = list(rng.normal(loc=0.0005, scale=0.01, size=300))
        out = self._tail(serie)
        arr = np.asarray(serie)
        q05 = float(np.quantile(arr, 0.05, method="linear"))
        assert out["var_95_daily"] == pytest.approx(-q05, rel=1e-12)
        assert out["cvar_95_daily"] == pytest.approx(-float(arr[arr <= q05].mean()), rel=1e-12)
        assert out["n_tail"] == int((arr <= q05).sum())
        assert out["n_tail"] >= 1

    def test_cvar_ge_var_seeded_random(self):
        rng = np.random.default_rng(0)
        serie = list(rng.normal(size=500))
        out = self._tail(serie)
        assert out["cvar_95_daily"] >= abs(out["var_95_daily"]) - 1e-15
        # Daily horizon, never annualized with sqrt(252):
        assert 0.0 < out["var_95_daily"] < 3.0

    def test_drawdown_pin_and_calmar_mean_t(self):
        serie = [0.01, 0.02, -0.05, 0.03, -0.01]
        out = self._dd(serie)
        arr = np.asarray(serie)
        wealth = np.exp(np.cumsum(arr))
        dd = wealth / np.maximum.accumulate(wealth) - 1.0
        assert out["max_drawdown"] == pytest.approx(float(dd.min()), rel=1e-12)
        assert out["max_drawdown"] <= 0.0
        assert out["annualized_return"] == pytest.approx(float(arr.mean() * 252), rel=1e-12)
        assert out["calmar_ratio"] == pytest.approx(
            float(arr.mean() * 252) / abs(float(dd.min())), rel=1e-12
        )

    def test_drawdown_flat_none_never_inf(self):
        out = self._dd([0.001] * 100)
        assert out["max_drawdown"] == pytest.approx(0.0, abs=1e-15)
        assert out["calmar_ratio"] is None
        assert out["reason"]

    def test_drawdown_negative_calmar_legal(self):
        out = self._dd([-0.02] * 100)
        assert out["max_drawdown"] < 0.0
        assert out["calmar_ratio"] is not None
        assert out["calmar_ratio"] < 0.0

    def test_sections_survive_strict_json(self, tmp_path):
        from portfolio_engine.app.report_json import dump_technical_report

        tail = self._tail([0.001] * 100)
        dd = self._dd([0.001] * 100)
        target = tmp_path / "risk.json"
        dump_technical_report({"tail": tail, "drawdown": dd}, target)
        loaded = _strict_loads(target.read_text(encoding="utf-8"))
        assert loaded["tail"]["sortino_ratio"] is None or isinstance(
            loaded["tail"]["sortino_ratio"], float
        )
        assert loaded["drawdown"]["calmar_ratio"] is None


class TestExportSurface:
    def test_compute_filter_rejections_exported(self):
        import portfolio_engine.app as app

        assert hasattr(app, "compute_filter_rejections")


class TestEnvelope:
    def test_envelope_minimum_is_schema_version_one(self):
        from portfolio_engine.app.report_json import build_report_envelope
        from portfolio_engine.core.config import PortfolioConfig

        envelope = build_report_envelope(
            ["AAA"], PortfolioConfig(), "2021-01-01", "2026-01-01",
            generated_at="2026-09-09T00:00:00+00:00",
        )
        assert envelope["schema_version"] == 1
        assert envelope["universe"] == ["AAA"]
        assert envelope["window"] == {"start": "2021-01-01", "end": "2026-01-01"}
        assert envelope["fingerprint"]
        assert envelope["run_id"]
        assert envelope["generated_at"] == "2026-09-09T00:00:00+00:00"
        assert envelope["engine_version"]

    def test_envelope_strict_json_round_trip(self):
        from portfolio_engine.app.report_json import build_report_envelope, sanitize_json_payload
        from portfolio_engine.core.config import PortfolioConfig

        envelope = build_report_envelope(
            ["AAA"], PortfolioConfig(), "2021-01-01", "2026-01-01",
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        text = json.dumps(sanitize_json_payload(envelope), allow_nan=False, sort_keys=True)
        assert _strict_loads(text)["schema_version"] == 1

    def test_module_exports_exposed_from_app_layer(self):
        import portfolio_engine.app as app

        for name in (
            "sanitize_json_payload",
            "dump_technical_report",
            "config_fingerprint",
            "build_report_envelope",
        ):
            assert hasattr(app, name), name
