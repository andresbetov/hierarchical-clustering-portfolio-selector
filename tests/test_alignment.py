"""Deterministic offline tests for calendar alignment (A3)."""

import numpy as np
import pytest

from portfolio_engine.core.metrics import (
    MIN_COMMON_ROWS,
    align_prices_to_common_calendar,
    construct_returns_matrix,
)


def _series_with_missing_middle(n: int, missing_idx: int):
    """Build (prices, dates) with one date removed in the middle."""
    base_dates = np.array(
        np.datetime64("2024-01-01") + np.arange(n + 1, dtype="timedelta64[D]"),
        dtype="datetime64[ns]",
    )
    prices_full = 100.0 + np.arange(n + 1, dtype=np.float64)
    dates = np.delete(base_dates, missing_idx)
    prices = np.delete(prices_full, missing_idx)
    return prices, dates


class TestAlignCommonCalendar:
    def test_short_ticker_trims_everyone(self):
        p_a = np.array([100.0, 101.0, 102.0, 103.0])
        d_a = np.array(
            np.datetime64("2024-01-01") + np.arange(4, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        # Ticker B starts one day later: common calendar = last 3 days of A.
        p_b, d_b = p_a[1:].copy(), d_a[1:]

        aligned = align_prices_to_common_calendar({"A": p_a, "B": p_b}, {"A": d_a, "B": d_b})

        assert aligned["A"].shape == aligned["B"].shape == (3,)
        # Intersection rows are B's full history positioned identically for A.
        assert np.allclose(aligned["A"], [101.0, 102.0, 103.0])
        assert np.allclose(aligned["B"], [101.0, 102.0, 103.0])

    def test_gap_in_middle_is_dropped_not_ffilled(self):
        # A has a hole at index 2; B has none -> intersection drops that day.
        p_a, d_a = _series_with_missing_middle(5, missing_idx=2)
        p_b = 200.0 + np.arange(len(d_b := np.array(
            np.datetime64("2024-01-01") + np.arange(6, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )))
        aligned = align_prices_to_common_calendar({"A": p_a, "B": p_b}, {"A": d_a, "B": d_b})

        assert len(aligned["A"]) == len(p_a)  # 5 common rows
        assert np.allclose(aligned["A"], p_a)  # ordered ascending

    def test_disjoint_calendars_raise(self):
        d_2023 = np.array(
            np.datetime64("2023-01-01") + np.arange(10, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        d_2024 = np.array(
            np.datetime64("2024-01-01") + np.arange(10, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        with pytest.raises(ValueError, match="too small|intersection"):
            align_prices_to_common_calendar(
                {"A": np.ones(10), "B": np.ones(10)}, {"A": d_2023, "B": d_2024}
            )

    def test_min_common_rows_enforced(self):
        tiny_date = np.array([np.datetime64("2024-01-02", "ns")])
        common_pair = {"d1": tiny_date, "d2": tiny_date}
        with pytest.raises(ValueError, match=f"{MIN_COMMON_ROWS}"):
            align_prices_to_common_calendar(
                {"A": np.array([1.0]), "B": np.array([2.0])},
                {"A": common_pair["d1"][:1], "B": common_pair["d2"][:1]},
            )

    def test_length_mismatch_between_prices_and_dates_raises(self):
        d_two = np.array(
            np.datetime64("2024-01-01") + np.arange(2, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        with pytest.raises(ValueError, match="prices vs"):
            align_prices_to_common_calendar(
                {"A": np.array([100.0, 101.0, 102.0])}, {"A": d_two}
            )

    def test_missing_dates_entry_raises(self):
        with pytest.raises(ValueError, match="Missing dates"):
            align_prices_to_common_calendar(
                {"A": np.array([1.0])}, {"B": np.array([1.0])}
            )


class TestConstructReturnsMatrixGuard:
    def test_misaligned_lengths_now_raise_loudly(self):
        with pytest.raises(ValueError, match="lengths differ"):
            construct_returns_matrix({
                "A": np.array([100.0, 101.0]),
                "B": np.array([200.0, 201.0, 202.0]),
            })

    def test_equal_length_legacy_behavior_intact(self):
        returns = construct_returns_matrix({
            "A": np.array([100.0, 101.0, 103.0]),
            "B": np.array([200.0, 202.0, 205.0]),
        })
        assert returns.shape == (2, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
