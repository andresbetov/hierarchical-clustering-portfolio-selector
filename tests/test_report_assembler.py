"""feat-050 contract: report assembler + pipeline/CLI integration (TDD red-first)."""

import json

import pytest


def _raise_constant(value):
    raise ValueError(f"non-standard JSON constant in report: {value}")


def _strict_loads(text):
    return json.loads(text, parse_constant=_raise_constant)


@pytest.fixture
def panel4(patched_batch):
    """4 healthy tickers, 800 rows — real engine route, offline."""
    tickers = ["E1", "E2", "E3", "E4"]
    patched_batch({t: {} for t in tickers}, rows=800)
    return tickers


def _run(tickers, tmp_path, monkeypatch, **kwargs):
    from portfolio_engine.app.pipeline import generate_complete_analysis_report
    from portfolio_engine.core.config import PortfolioConfig

    monkeypatch.chdir(tmp_path)
    return generate_complete_analysis_report(
        tickers, PortfolioConfig(), save_plots=False, show_plots=False, **kwargs
    )


class TestAssemblerEmission:
    def test_default_writes_nothing(self, panel4, tmp_path, monkeypatch):
        result = _run(panel4, tmp_path, monkeypatch)
        assert isinstance(result, tuple) and len(result) == 4
        assert not (tmp_path / "reports").exists()

    def test_e2e_writes_strict_json_all_sections(self, panel4, tmp_path, monkeypatch):
        from portfolio_engine.app.report_json import config_fingerprint
        from portfolio_engine.core.config import PortfolioConfig

        target = tmp_path / "r" / "tech.json"
        _run(panel4, tmp_path, monkeypatch, report_path=target)
        doc = _strict_loads(target.read_text(encoding="utf-8"))
        assert doc["envelope"]["schema_version"] == 1
        for key in ("envelope", "filter_rejections", "allocation_diagnostics",
                    "risk", "tree_diagnostics", "walk_forward"):
            assert key in doc, key
        assert doc["walk_forward"] is None
        assert doc["risk"]["tail"]["frequency"] == "daily"
        assert doc["risk"]["drawdown"]["sample"] == "in-sample"
        assert isinstance(doc["risk"]["series_n_obs"], int)
        expected = config_fingerprint(
            PortfolioConfig(), panel4,
            doc["envelope"]["window"]["start"], doc["envelope"]["window"]["end"],
        )
        assert doc["envelope"]["fingerprint"] == expected
        assert doc["envelope"]["run_id"] == expected

    def test_report_failure_warns_and_returns_tuple(self, panel4, tmp_path, monkeypatch, caplog):
        import portfolio_engine.app.report_json as report_json_module

        def _boom(payload, path):
            raise OSError("disk gone")

        monkeypatch.setattr(report_json_module, "dump_technical_report", _boom)
        with caplog.at_level("WARNING", logger="portfolio_engine.app.pipeline"):
            result = _run(panel4, tmp_path, monkeypatch, report_path=tmp_path / "r.json")
        assert isinstance(result, tuple) and len(result) == 4
        assert any("Technical report JSON skipped" in r.message for r in caplog.records)

    def test_no_save_still_emits_json(self, panel4, tmp_path, monkeypatch):
        target = tmp_path / "r.json"
        _run(panel4, tmp_path, monkeypatch, report_path=target)
        assert target.exists()
        assert not (tmp_path / "charts").exists()  # save_plots=False: no dir at all

    def test_empty_universe_public_path_emits_nulls(self, tmp_path, monkeypatch, patched_batch):
        """Early-exit (N=0) honors report_path: valid mostly-null JSON."""
        from portfolio_engine.app.pipeline import generate_complete_analysis_report
        from portfolio_engine.core.config import PortfolioConfig

        patched_batch({"F1": {"flat": True}, "F2": {"flat": True}}, rows=800)
        monkeypatch.chdir(tmp_path)
        result = generate_complete_analysis_report(
            ["F1", "F2"], PortfolioConfig(), save_plots=False, show_plots=False,
            report_path=tmp_path / "empty.json")
        assert isinstance(result, tuple) and len(result) == 4
        assert result[3] == {}
        doc = _strict_loads((tmp_path / "empty.json").read_text(encoding="utf-8"))
        assert doc["envelope"]["schema_version"] == 1
        assert doc["allocation_diagnostics"]["hhi"] is None
        assert doc["walk_forward"] is None

    def test_builder_failure_warns_not_dump_only(self, panel4, tmp_path, monkeypatch, caplog):
        """Warning net covers build failures too, not just dump failures."""
        import portfolio_engine.app.report_json as report_json_module

        def _boom(*args, **kwargs):
            raise ValueError("builder blew up")

        monkeypatch.setattr(report_json_module, "build_technical_report", _boom)
        with caplog.at_level("WARNING", logger="portfolio_engine.app.pipeline"):
            result = _run(panel4, tmp_path, monkeypatch, report_path=tmp_path / "r.json")
        assert isinstance(result, tuple) and len(result) == 4
        assert any("Technical report JSON skipped" in r.message for r in caplog.records)

    def test_run_results_identical_with_and_without_report(self, panel4, tmp_path, monkeypatch):
        from portfolio_engine.app.pipeline import generate_complete_analysis_report
        from portfolio_engine.core.config import PortfolioConfig

        monkeypatch.chdir(tmp_path)
        plain = generate_complete_analysis_report(
            panel4, PortfolioConfig(), save_plots=False, show_plots=False)
        with_report = generate_complete_analysis_report(
            panel4, PortfolioConfig(), save_plots=False, show_plots=False,
            report_path=tmp_path / "r.json")
        assert [type(v) for v in plain] == [type(v) for v in with_report]
        assert plain[2].keys() == with_report[2].keys()  # metrics dicts (ndarray values: no ==)
        assert plain[3] == with_report[3]  # weights dict of floats

    def test_empty_universe_report_valid(self):
        """N=0 filtered: every section degrades to null, document stays valid."""
        import numpy as np

        from portfolio_engine.app.report_json import build_technical_report
        from portfolio_engine.core.config import PortfolioConfig

        cfg = PortfolioConfig()
        doc = build_technical_report(
            requested_tickers=["ZZ"],
            asset_metrics={"ZZ": {"sharpe_ratio": 0.01, "annual_volatility": 0.5}},
            filtered_metrics={},
            closing_prices={"ZZ": np.array([100.0, 101.0, 102.0])},
            price_dates={"ZZ": ["2024-01-01", "2024-01-02", "2024-01-03"]},
            covariance_matrix=np.empty((0, 0)),
            covariance_tickers=[],
            weights={},
            config=cfg,
            window_start="2024-01-01",
            window_end="2024-01-03",
            generated_at="2026-09-10T00:00:00+00:00",
        )
        assert doc["allocation_diagnostics"]["hhi"] is None
        assert doc["risk"]["tail"]["sortino_ratio"] is None
        assert doc["tree_diagnostics"]["max_depth"] is None
        assert doc["walk_forward"] is None
        assert doc["filter_rejections"]["counts"]["requested"] == 1
        _strict_loads(json.dumps(doc, sort_keys=True))


class TestCliWiring:
    def test_cli_writes_default_report_path(self, tmp_path, monkeypatch, patched_batch):
        import portfolio_engine.cli as cli_module

        patched_batch({"C1": {}, "C2": {}}, rows=800)
        (tmp_path / "universe.yaml").write_text(
            "universe:\n  - C1\n  - C2\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        cli_module.main(argv=["--universe", str(tmp_path / "universe.yaml"), "--no-save"])
        target = tmp_path / "reports" / "technical-report.json"
        assert target.exists()
        doc = _strict_loads(target.read_text(encoding="utf-8"))
        assert doc["envelope"]["schema_version"] == 1

    def test_build_technical_report_exported(self):
        import portfolio_engine as top

        assert hasattr(top, "build_technical_report")
        assert hasattr(top, "dump_technical_report")
