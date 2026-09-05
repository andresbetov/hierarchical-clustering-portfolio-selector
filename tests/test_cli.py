"""Packaging identity tests — the contract is behavior, not pyproject text.

These never invoke cli.main() (it would hit the network); they assert the
distribution metadata resolves and the entrypoint wiring is exact.
"""

import importlib.metadata

import pytest

DIST_NAME = "hierarchical-clustering-portfolio-selector"


def test_distribution_resolves():
    assert importlib.metadata.version(DIST_NAME) == "0.1.0"


def test_console_script_entrypoint_wiring():
    eps = [
        ep
        for ep in importlib.metadata.entry_points(group="console_scripts")
        if ep.name == "portfolio-run"
    ]
    assert len(eps) == 1, f"expected exactly one portfolio-run, got {len(eps)}"
    assert eps[0].value == "portfolio_engine.cli:main"


def test_cli_main_importable_without_path_hacks():
    from portfolio_engine.cli import main  # noqa: F401  (import is the assertion)

    # B2: the hardcoded universe moved to config/universe.yaml via load_universe.
    from portfolio_engine.data.universe import DEFAULT_UNIVERSE_PATH

    assert str(DEFAULT_UNIVERSE_PATH) == "config/universe.yaml"


def test_cli_refresh_cache_flag_parsing():
    from portfolio_engine.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args([])
    assert args.refresh_cache is False
    args2 = parser.parse_args(["--refresh-cache"])
    assert args2.refresh_cache is True
    # --help docs flag (implicit via parser, no raise)
    assert "--refresh-cache" in parser.format_help()


def test_cli_refresh_cache_propagates_to_provider(monkeypatch):
    from portfolio_engine import cli as cli_module

    captured: dict = {}

    def fake_report(universe, config, save_plots=True, show_plots=False, provider=None):
        captured["provider"] = provider
        return {}, {}, {}, {}

    def fake_load_universe(path):
        return ["AAA"]

    monkeypatch.setattr(cli_module, "generate_complete_analysis_report", fake_report)
    monkeypatch.setattr(cli_module, "load_universe", fake_load_universe)

    # without flag
    cli_module.main(argv=[])
    assert captured["provider"] is not None
    assert captured["provider"].refresh_cache is False

    # with flag
    cli_module.main(argv=["--refresh-cache"])
    assert captured["provider"].refresh_cache is True

    # legacy universe_path bypasses CLI parsing and forces refresh False
    cli_module.main(universe_path="config/universe.yaml")
    assert captured["provider"].refresh_cache is False


def test_cli_method_flag_exists_and_propagates():
    from portfolio_engine.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["--method", "hrp"])
    assert args.weight_allocation_method == "hrp"
    args2 = parser.parse_args(["--method", "risk_parity"])
    assert args2.weight_allocation_method == "risk_parity"
    with pytest.raises(SystemExit):
        parser.parse_args(["--method", "risk_parit"])


def test_cli_covariance_estimator_flag():
    from portfolio_engine.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["--covariance-estimator", "ledoit_wolf"])
    assert args.covariance_estimator == "ledoit_wolf"
    with pytest.raises(SystemExit):
        parser.parse_args(["--covariance-estimator", "bad"])


def test_cli_linkage_flag():
    from portfolio_engine.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args(["--linkage", "ward"])
    assert args.linkage_method == "ward"
    args2 = parser.parse_args(["--linkage-method", "average"])
    assert args2.linkage_method == "average"
    with pytest.raises(SystemExit):
        parser.parse_args(["--linkage", "centroid"])


def test_cli_save_show_flags():
    from portfolio_engine.cli import _build_parser

    parser = _build_parser()
    args = parser.parse_args([])
    assert args.save is True
    assert args.show is False
    assert "--save" in parser.format_help()
    assert "--show" in parser.format_help()
    no_save = parser.parse_args(["--no-save"])
    assert no_save.save is False
    show = parser.parse_args(["--show"])
    assert show.show is True
    no_show = parser.parse_args(["--no-show"])
    assert no_show.show is False


def test_cli_help_documents_all_flags():
    from portfolio_engine.cli import _build_parser

    text = _build_parser().format_help()
    expected = [
        "--universe",
        "--method",
        "--covariance-estimator",
        "--linkage",
        "--save",
        "--show",
        "--refresh-cache",
    ]
    for flag in expected:
        assert flag in text


def test_cli_propagates_all_to_config(monkeypatch):
    from portfolio_engine import cli as cli_module

    captured: dict = {}

    def fake_report(universe, config, save_plots=True, show_plots=False, provider=None):
        captured["config"] = config
        captured["save_plots"] = save_plots
        captured["show_plots"] = show_plots
        captured["provider"] = provider
        captured["universe"] = universe
        return {}, {}, {}, {}

    def fake_load(path):
        return ["AAA"]

    monkeypatch.setattr(cli_module, "generate_complete_analysis_report", fake_report)
    monkeypatch.setattr(cli_module, "load_universe", fake_load)

    cli_module.main(
        argv=[
            "--method",
            "risk_parity",
            "--covariance-estimator",
            "oas",
            "--linkage",
            "ward",
            "--no-save",
            "--show",
        ]
    )
    assert captured["config"].weight_allocation_method == "risk_parity"
    assert captured["config"].covariance_estimator == "oas"
    assert captured["config"].linkage_method == "ward"
    assert captured["save_plots"] is False
    assert captured["show_plots"] is True


def test_cli_defaults_propagate(monkeypatch):
    from portfolio_engine import cli as cli_module

    captured: dict = {}

    def fake_report(universe, config, save_plots=True, show_plots=False, provider=None):
        captured["config"] = config
        captured["save_plots"] = save_plots
        captured["show_plots"] = show_plots
        return {}, {}, {}, {}

    monkeypatch.setattr(cli_module, "generate_complete_analysis_report", fake_report)
    monkeypatch.setattr(cli_module, "load_universe", lambda p: ["AAA"])

    cli_module.main(argv=[])
    assert captured["config"].weight_allocation_method == "hrp"
    assert captured["config"].covariance_estimator == "sample"
    assert captured["config"].linkage_method == "single"
    assert captured["save_plots"] is True
    assert captured["show_plots"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
