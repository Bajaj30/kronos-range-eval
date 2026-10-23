import numpy as np
import pandas as pd
import pytest

from lib.features import add_target_and_baselines
from lib.forecast import sample_tr_pct, summarise
from lib.runs import StaleCache, cached_samples, forecast_table
from tests.test_01_features import synthetic


def test_inverted_sampled_bar_uses_max_and_min_of_all_four_prices():
    # open 100, "high" 98 (below the open), "low" 103 (above the high), close 101; previous close 100.
    # Real high = 103, real low = 98 -> TR = max(103, 100) - min(98, 100) = 5 -> 5%.
    assert sample_tr_pct(np.array([[100.0, 98.0, 103.0, 101.0]]), 100.0) == pytest.approx([5.0], rel=1e-15)


def test_sampled_gap_counts_from_the_previous_close():
    # The whole sampled bar sits above the previous close: TR = 106 - 100 = 6 -> 6% (high - low alone would say 2%).
    assert sample_tr_pct(np.array([[105.0, 106.0, 104.0, 105.5]]), 100.0) == pytest.approx([6.0], rel=1e-15)


def test_shapes_days_by_samples():
    samples = np.random.default_rng(0).uniform(99, 101, size=(7, 30, 4))
    tr = sample_tr_pct(samples, np.full(7, 100.0))
    assert tr.shape == (7, 30)
    s = summarise(tr)
    assert all(s[k].shape == (7,) for k in ("p10", "median", "p90", "distinct"))
    assert (s["p10"] <= s["median"]).all() and (s["median"] <= s["p90"]).all()


def test_quantiles_are_linear_interpolation_hand_values():
    s = summarise(np.arange(1.0, 11.0)[None, :])  # 1..10: position (n - 1) * q
    assert (s["p10"][0], s["median"][0], s["p90"][0]) == pytest.approx((1.9, 5.5, 9.1), rel=1e-12)
    assert s["distinct"][0] == 10


def test_bad_inputs_are_refused():
    with pytest.raises(ValueError, match="open, high, low, close"):
        sample_tr_pct(np.zeros((2, 3)), 100.0)
    with pytest.raises(ValueError, match="NaN"):
        summarise(np.array([[1.0, np.nan]]))


def test_forecast_table_measures_samples_against_the_previous_rows_close():
    """Flat sampled bars at day t's actual close: the forecast must equal |C_t - C_t-1| / C_t-1 (an off-by-one
    in the previous close would break this)."""
    bars = add_target_and_baselines(synthetic(), atr_period=14)
    days = bars["date"].iloc[[20, 21, 30]]
    flat = np.repeat(bars["close"].iloc[[20, 21, 30]].to_numpy()[:, None, None], 4, axis=2).repeat(5, axis=1)
    table = forecast_table(bars, days, flat)
    expected = (bars["close"].diff().abs() / bars["close"].shift(1) * 100).iloc[[20, 21, 30]].to_numpy()
    np.testing.assert_allclose(table["kronos_median"], expected, rtol=1e-12)
    np.testing.assert_array_equal(table["tr_pct"], bars["tr_pct"].iloc[[20, 21, 30]])


def test_cache_reuses_only_identical_settings(tmp_path):
    path = tmp_path / "s.npz"
    calls = []
    make = lambda: calls.append(1) or np.ones((2, 3, 4), dtype=np.float32)  # noqa: E731
    a, computed_a = cached_samples(path, {"T": 1.0, "n": 3}, make)
    b, computed_b = cached_samples(path, {"T": 1.0, "n": 3}, make)
    assert (computed_a, computed_b, len(calls)) == (True, False, 1)
    np.testing.assert_array_equal(a, b)
    with pytest.raises(StaleCache, match="T"):
        cached_samples(path, {"T": 0.6, "n": 3}, make)
    assert [p.name for p in tmp_path.iterdir()] == ["s.npz"]  # no partial file left behind
