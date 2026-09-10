"""B2 contract tests: external universe loading with validated schema."""

import pytest

from portfolio_engine.data.universe import load_universe


def _write_universe(tmp_path, content):
    target = tmp_path / "universe.yaml"
    target.write_text(content, encoding="utf-8")
    return target


class TestLoadUniverse:
    def test_valid_yaml_uppercased_and_stripped(self, tmp_path):
        target = _write_universe(
            tmp_path,
            "universe:\n  - aapl\n  - MSFT   # comment\n  - jnj\n",
        )
        assert load_universe(target) == ["AAPL", "MSFT", "JNJ"]

    def test_missing_file_raises_named(self, tmp_path):
        with pytest.raises(ValueError, match="not found"):
            load_universe(tmp_path / "nope.yaml")

    def test_missing_top_level_key_rejected(self, tmp_path):
        target = _write_universe(tmp_path, "tickers:\n  - AAPL\n")
        with pytest.raises(ValueError, match="'universe' key"):
            load_universe(target)

    def test_non_list_rejected(self, tmp_path):
        target = _write_universe(tmp_path, "universe: AAPL\n")
        with pytest.raises(ValueError, match="non-empty list"):
            load_universe(target)

    def test_empty_list_rejected(self, tmp_path):
        target = _write_universe(tmp_path, "universe: []\n")
        with pytest.raises(ValueError, match="non-empty list"):
            load_universe(target)

    def test_non_string_entries_rejected(self, tmp_path):
        target = _write_universe(tmp_path, "universe:\n  - 123\n")
        with pytest.raises(ValueError, match="strings"):
            load_universe(target)

    def test_default_repo_universe_loads_twelve_us_names(self):
        from portfolio_engine.data.universe import DEFAULT_UNIVERSE_PATH

        universe = load_universe(DEFAULT_UNIVERSE_PATH)
        assert len(universe) == 12
        assert "JNJ" in universe and universe == [t.upper() for t in universe]
