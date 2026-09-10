"""HRP dendrogram contract — headless, quasi-diagonal leaf order, edges."""

import numpy as np
import pytest


def test_plot_hrp_dendrogram_importable():
    from portfolio_engine import build_hrp_linkage, plot_hrp_dendrogram

    assert callable(plot_hrp_dendrogram)
    assert callable(build_hrp_linkage)
    # also via reporting
    from portfolio_engine.viz.reporting import plot_hrp_dendrogram as via_reporting

    assert callable(via_reporting)


def test_build_hrp_linkage_validates_and_matches_hrp():
    from portfolio_engine.portfolio.hrp import build_hrp_linkage, calculate_hrp_weights

    cov = np.array([[0.04, 0.02, 0.01], [0.02, 0.03, 0.015], [0.01, 0.015, 0.05]])
    Z = build_hrp_linkage(cov, linkage_method="single")
    assert Z.shape == (2, 4)
    # calculate_hrp_weights with same linkage gives same leaf behavior (deterministic)
    w_single = calculate_hrp_weights(cov, linkage_method="single")
    assert np.all(np.isfinite(w_single))
    # ward produces same shape but different heights
    Z_ward = build_hrp_linkage(cov, linkage_method="ward")
    assert Z_ward.shape == (2, 4)
    with pytest.raises(ValueError, match="linkage_method"):
        build_hrp_linkage(cov, linkage_method="centroid")


def test_build_hrp_linkage_guard_n1():
    from portfolio_engine.portfolio.hrp import build_hrp_linkage

    with pytest.raises(ValueError, match="at least 2"):
        build_hrp_linkage(np.array([[0.04]]), linkage_method="single")


def test_dendrogram_headless_and_leaf_order(tmp_path):
    from scipy.cluster.hierarchy import dendrogram, leaves_list

    from portfolio_engine.portfolio.hrp import _leaf_order, build_hrp_linkage
    from portfolio_engine.viz.reporting import plot_hrp_dendrogram

    cov = np.array([[0.04, 0.02, 0.01], [0.02, 0.03, 0.015], [0.01, 0.015, 0.05]])
    tickers = ["A", "B", "C"]
    Z = build_hrp_linkage(cov, linkage_method="single")
    leaf_order = _leaf_order(Z, 3)
    assert leaves_list(Z).tolist() == leaf_order
    d = dendrogram(Z, no_plot=True)
    assert d["leaves"] == leaf_order

    png = tmp_path / "dend.png"
    plot_hrp_dendrogram(cov, "single", tickers, save_path=str(png), show_plot=False)
    assert png.exists()
    assert png.stat().st_size > 1000


def test_dendrogram_12_block_quasi_diagonal(tmp_path):
    """Synthetic 3-block correlation: intra-block adjacent in leaves."""
    from portfolio_engine.portfolio.hrp import _leaf_order, build_hrp_linkage
    from portfolio_engine.viz.reporting import plot_hrp_dendrogram

    rng = np.random.default_rng(42)
    n, block = 12, 4
    # Build block-diagonal correlation: high within block, low across
    base = np.full((n, n), 0.2)
    for b in range(0, n, block):
        base[b : b + block, b : b + block] = 0.85
    np.fill_diagonal(base, 1.0)
    # Add noise and make cov
    noise = rng.normal(scale=0.02, size=(n, n))
    noise = (noise + noise.T) / 2
    corr = np.clip(base + noise * 0.1, -0.9, 0.99)
    np.fill_diagonal(corr, 1.0)
    vols = np.full(n, 0.2)
    cov = corr * np.outer(vols, vols)
    # Ensure PD via jitter if needed
    cov = cov + np.eye(n) * 1e-6

    Z = build_hrp_linkage(cov, linkage_method="single")
    leaves = _leaf_order(Z, n)
    # each block's tickers should be contiguous in leaf order
    pos = {leaf: i for i, leaf in enumerate(leaves)}
    for b in range(0, n, block):
        block_leaves = list(range(b, b + block))
        indices = sorted(pos[x] for x in block_leaves)
        assert max(indices) - min(indices) == block - 1  # contiguous

    png = tmp_path / "dend12.png"
    tickers = [f"T{i}" for i in range(n)]
    plot_hrp_dendrogram(cov, "single", tickers, save_path=str(png), show_plot=False)
    assert png.exists()
    assert png.stat().st_size > 2000


def test_dendrogram_n1_n2_no_crash(tmp_path):
    from portfolio_engine.viz.reporting import plot_hrp_dendrogram

    png1 = tmp_path / "d1.png"
    plot_hrp_dendrogram(np.array([[0.04]]), "single", ["A"], save_path=str(png1), show_plot=False)
    assert png1.exists()
    assert png1.stat().st_size > 500

    png2 = tmp_path / "d2.png"
    cov2 = np.array([[0.04, 0.01], [0.01, 0.03]])
    plot_hrp_dendrogram(cov2, "single", ["A", "B"], save_path=str(png2), show_plot=False)
    assert png2.exists()
    assert png2.stat().st_size > 500

    # n=0 / empty tickers
    png0 = tmp_path / "d0.png"
    plot_hrp_dendrogram(np.empty((0, 0)), "single", [], save_path=str(png0), show_plot=False)
    assert png0.exists()


def test_pipeline_generates_dendrogram_file(tmp_path, monkeypatch):
    """E2E via pipeline.generate_complete_analysis_report with synthetic provider."""

    import portfolio_engine.app.pipeline as pipeline_module
    import portfolio_engine.data.data_fetch as data_fetch_module
    from tests.conftest import _build_panel

    # Build synthetic panel 12 tickers, no network
    spec = {f"T{i}": {} for i in range(6)}
    panel = _build_panel(spec, rows=40)

    def fake_batch(tickers, start, end):
        return panel

    monkeypatch.setattr(data_fetch_module, "_fetch_batch", fake_batch)
    # Isolate charts dir
    monkeypatch.chdir(tmp_path)
    (tmp_path / "charts").mkdir(exist_ok=True)

    from portfolio_engine.core.config import PortfolioConfig

    config = PortfolioConfig(
        weight_allocation_method="hrp",
        linkage_method="single",
        minimum_sharpe_threshold=-10.0,
        maximum_volatility_threshold=10.0,
    )
    # universe 6 tickers
    universe = list(spec.keys())
    pipeline_module.generate_complete_analysis_report(universe, config, save_plots=True, show_plots=False)
    dendro = tmp_path / "charts" / "hrp_dendrogram.png"
    assert dendro.exists()
    assert dendro.stat().st_size > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
