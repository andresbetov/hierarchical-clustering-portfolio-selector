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

    def test_export_surface_allocation_diagnostics(self):
        import portfolio_engine.app as app

        assert hasattr(app, "allocation_diagnostics")


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
