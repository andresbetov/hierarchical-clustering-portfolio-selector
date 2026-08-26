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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
