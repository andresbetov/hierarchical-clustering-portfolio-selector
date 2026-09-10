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
    }

    def _classify(self):
        from portfolio_engine.app.report_json import compute_filter_rejections
        from portfolio_engine.core.config import PortfolioConfig

        return compute_filter_rejections(
            requested_tickers=["GOOD", "EDGE", "VOLBAD", "NANSHARPE", "NANVOL", "OVERLAP", "PRUNED", "GHOST"],
            asset_metrics=self.METRICS,
            filtered_metrics={"GOOD": self.METRICS["GOOD"], "OVERLAP": self.METRICS["OVERLAP"]},
            closing_prices={t: np.array([100.0]) for t in self.METRICS},
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

    def test_thresholds_and_counts_consistent(self):
        report = self._classify()
        assert report["thresholds"] == {"min_sharpe": 0.3, "max_volatility": 0.27}
        counts = report["counts"]
        assert counts == {"requested": 8, "kept": 2, "rejected": 6}
        assert counts["kept"] + counts["rejected"] == counts["requested"]
        assert set(report["tickers"]) == {
            "GOOD", "EDGE", "VOLBAD", "NANSHARPE", "NANVOL", "OVERLAP", "PRUNED", "GHOST",
        }

    def test_derived_reasons_match_production_filter(self):
        """Reason parity vs production: every classification the report derives
        must be derivable from the SAME guard order apply_asset_filters uses
        (non-finite -> sharpe -> vol), plus the calendar-prune layer that the
        final filtered set encodes."""
        from portfolio_engine.portfolio.selection import apply_asset_filters

        production_filtered, _ = apply_asset_filters(
            {t: dict(m) for t, m in self.METRICS.items()},
            {t: np.array([100.0]) for t in self.METRICS},
            0.3,
            0.27,
        )
        assert set(production_filtered) == {"GOOD", "OVERLAP", "PRUNED"}
        report = self._classify()
        classify_filtered = {"GOOD", "OVERLAP"}
        for ticker, metrics in self.METRICS.items():
            if not np.isfinite(metrics["sharpe_ratio"]):
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

    def test_reasons_survive_strict_json_serialization(self):
        from portfolio_engine.app.report_json import dump_technical_report

        target = Path(tmp_reports_dir())
        dump_technical_report({"filtering": self._classify()}, target / "r.json")
        loaded = _strict_loads((target / "r.json").read_text(encoding="utf-8"))
        assert loaded["filtering"]["counts"]["kept"] == 2


def tmp_reports_dir():
    import tempfile

    return Path(tempfile.mkdtemp())


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
