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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
