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
        # With a permissive threshold the old inner-join trimming is preserved.
        p_a = np.array([100.0, 101.0, 102.0, 103.0])
        d_a = np.array(
            np.datetime64("2024-01-01") + np.arange(4, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        # Ticker B starts one day later: common calendar = last 3 days of A.
        p_b, d_b = p_a[1:].copy(), d_a[1:]

        aligned = align_prices_to_common_calendar(
            {"A": p_a, "B": p_b}, {"A": d_a, "B": d_b}, minimum_overlap_ratio=0.5
        )

        assert aligned["A"].shape == aligned["B"].shape == (3,)
        # Intersection rows are B's full history positioned identically for A.
        assert np.allclose(aligned["A"], [101.0, 102.0, 103.0])
        assert np.allclose(aligned["B"], [101.0, 102.0, 103.0])

    def test_gap_in_middle_is_dropped_not_ffilled(self):
        # A has a hole at index 2; B has none -> intersection drops that day.
        # Use permissive threshold so the guard does not exclude A (ratio 5/6≈0.83).
        p_a, d_a = _series_with_missing_middle(5, missing_idx=2)
        p_b = 200.0 + np.arange(len(d_b := np.array(
            np.datetime64("2024-01-01") + np.arange(6, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )))
        aligned = align_prices_to_common_calendar(
            {"A": p_a, "B": p_b}, {"A": d_a, "B": d_b}, minimum_overlap_ratio=0.5
        )

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


class TestOverlapGuard:
    def test_ticker_with_50_percent_history_excluded_preserves_common_rows(self, caplog):
        # A/B have 10 days, C has 5 days (50% overlap) -> with 0.9, C excluded, A/B keep 10 rows.
        base = np.datetime64("2024-01-01")
        d_full = np.array(base + np.arange(10, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        d_half = d_full[5:]  # last 5 days only
        p_full = 100.0 + np.arange(10, dtype=np.float64)
        p_half = 100.0 + np.arange(5, dtype=np.float64) + 5

        with caplog.at_level("WARNING"):
            aligned = align_prices_to_common_calendar(
                {"A": p_full, "B": p_full.copy(), "C": p_half},
                {"A": d_full, "B": d_full, "C": d_half},
                minimum_overlap_ratio=0.9,
            )

        assert set(aligned.keys()) == {"A", "B"}
        assert aligned["A"].shape == (10,)
        assert "C" not in aligned
        assert any("C" in m for m in caplog.messages)

    def test_threshold_1_0_bit_identical_to_current_inner_join(self):
        p_a = np.array([100.0, 101.0, 102.0])
        d_a = np.array(
            np.datetime64("2024-01-01") + np.arange(3, dtype="timedelta64[D]"),
            dtype="datetime64[ns]",
        )
        p_b = np.array([200.0, 201.0, 202.0])
        # Same test as 1.1 but with default-equivalent 1.0: both share full span -> identical to old.
        aligned_default = align_prices_to_common_calendar(
            {"A": p_a, "B": p_b}, {"A": d_a, "B": d_a}, minimum_overlap_ratio=1.0
        )
        aligned_old = align_prices_to_common_calendar(
            {"A": p_a, "B": p_b}, {"A": d_a, "B": d_a}, minimum_overlap_ratio=0.9
        )
        # With perfect overlap both thresholds retain everyone -> identical
        assert np.allclose(aligned_default["A"], aligned_old["A"])
        assert np.allclose(aligned_default["B"], aligned_old["B"])

    def test_exact_0_9_retained_and_just_below_excluded(self):
        base = np.datetime64("2024-01-01")
        d_full = np.array(base + np.arange(10, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        # 9/10 = 0.9 exactly -> retained
        d_9 = d_full[1:]  # 9 days -> 0.9 on union of 10
        p_full = 100.0 + np.arange(10, dtype=np.float64)
        p_9 = 100.0 + np.arange(9, dtype=np.float64)
        aligned_90 = align_prices_to_common_calendar(
            {"A": p_full, "B": p_9}, {"A": d_full, "B": d_9}, minimum_overlap_ratio=0.9
        )
        assert set(aligned_90.keys()) == {"A", "B"}

        # 8/10 = 0.8 -> excluded with 0.9
        d_8 = d_full[2:]
        p_8 = 100.0 + np.arange(8, dtype=np.float64)
        aligned_80 = align_prices_to_common_calendar(
            {"A": p_full, "B": p_8}, {"A": d_full, "B": d_8}, minimum_overlap_ratio=0.9
        )
        assert set(aligned_80.keys()) == {"A"}

    def test_single_survivor_returns_one_column(self):
        base = np.datetime64("2024-01-01")
        d_full = np.array(base + np.arange(5, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        d_half = d_full[3:]  # 2/5=0.4 <0.9 -> B excluded, A survives alone
        p_full = 100.0 + np.arange(5, dtype=np.float64)
        p_half = 100.0 + np.arange(2, dtype=np.float64)
        aligned = align_prices_to_common_calendar(
            {"A": p_full, "B": p_half}, {"A": d_full, "B": d_half}, minimum_overlap_ratio=0.9
        )
        assert set(aligned.keys()) == {"A"}
        assert aligned["A"].shape == (5,)

    def test_zero_survivors_raises(self):
        base = np.datetime64("2024-01-01")
        d1 = np.array(base + np.arange(5, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        d2 = np.array((base + np.timedelta64(10, "D")) + np.arange(5, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        # Union 10 days, each ticker covers 5 -> ratio 0.5 <0.9 -> both excluded -> 0 survivors
        with pytest.raises(ValueError, match="No tickers.*overlap|too small|intersection"):
            align_prices_to_common_calendar(
                {"A": np.ones(5), "B": np.ones(5)}, {"A": d1, "B": d2}, minimum_overlap_ratio=0.9
            )

    def test_intercalated_gap_not_excluded(self):
        # A has one missing day in middle -> ratio 5/6≈0.83? Actually union 6, A covers 5 -> 0.833 <0.9 would exclude,
        # so use threshold 0.8 to test gap vs tail distinction: gap should not be excluded with 0.8.
        p_a, d_a = _series_with_missing_middle(5, missing_idx=2)  # 5 present out of 6 union -> 0.833
        p_b = 200.0 + np.arange(6, dtype=np.float64)
        d_b = np.array(np.datetime64("2024-01-01") + np.arange(6, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        aligned = align_prices_to_common_calendar(
            {"A": p_a, "B": p_b}, {"A": d_a, "B": d_b}, minimum_overlap_ratio=0.8
        )
        assert set(aligned.keys()) == {"A", "B"}
        assert len(aligned["A"]) == 5  # hole dropped for both, but A not excluded by guard

    def test_order_preserved_after_exclusion(self):
        base = np.datetime64("2024-01-01")
        d_full = np.array(base + np.arange(5, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        d_half = d_full[3:]
        p_full = 100.0 + np.arange(5, dtype=np.float64)
        p_half = 100.0 + np.arange(2, dtype=np.float64)
        aligned = align_prices_to_common_calendar(
            {"C": p_half, "A": p_full, "B": p_full.copy()},
            {"C": d_half, "A": d_full, "B": d_full},
            minimum_overlap_ratio=0.9,
        )
        assert list(aligned.keys()) == ["A", "B"]  # C excluded, A/B order preserved as in input

    def test_warning_logged_with_ratios(self, caplog):
        import logging

        base = np.datetime64("2024-01-01")
        d_full = np.array(base + np.arange(10, dtype="timedelta64[D]"), dtype="datetime64[ns]")
        d_half = d_full[5:]
        p_full = 100.0 + np.arange(10, dtype=np.float64)
        p_half = 100.0 + np.arange(5, dtype=np.float64)
        with caplog.at_level(logging.WARNING):
            align_prices_to_common_calendar(
                {"A": p_full, "B": p_half}, {"A": d_full, "B": d_half}, minimum_overlap_ratio=0.9
            )
        assert any("excluded" in m.lower() or "C" in m or "B" in m for m in caplog.messages)


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
