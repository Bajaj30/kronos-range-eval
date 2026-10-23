import numpy as np
import pytest

from lib import metrics as M

Y = np.array([1.0, 2.0, 0.5, 1.5, 3.0])


def test_perfect_forecast_has_zero_error_and_full_coverage():
    s = M.score(Y, Y, Y, Y, alpha=0.2)
    assert s["mae"] == 0 and s["coverage"] == 1.0 and s["interval_score"] == 0


def test_forecast_two_times_too_small_gets_factor_exactly_two():
    assert M.fit_kronos(Y, Y / 2)["scale"] == 2.0
    cal = M.fit_baseline(Y, Y / 2)
    assert (cal["scale"], cal["band_lo"], cal["band_hi"]) == (2.0, 2.0, 2.0)
    point, lo, hi = M.apply_baseline(cal, Y / 2)
    np.testing.assert_array_equal(point, Y)


def test_calibration_uses_the_median_ratio_not_the_mean():
    assert M.fit_kronos([1.0, 2.0, 10.0], [1.0, 1.0, 1.0])["scale"] == 2.0  # mean would be 4.33


def test_kronos_band_scales_with_the_same_factor():
    point, lo, hi = M.apply_kronos({"scale": 1.5}, [2.0], [1.0], [4.0])
    assert (point[0], lo[0], hi[0]) == (3.0, 1.5, 6.0)


def test_calibration_refuses_zero_or_nan_forecasts():
    with pytest.raises(ValueError, match="positive"):
        M.fit_kronos([1.0, 2.0], [1.0, 0.0])
    with pytest.raises(ValueError, match="NaN"):
        M.fit_baseline([1.0, np.nan], [1.0, 1.0])


def test_coverage_includes_the_band_ends():
    assert M.coverage([1.0, 2.0, 3.0], [1.0, 1.0, 1.0], [3.0, 1.5, 3.0]) == pytest.approx(2 / 3)


def test_interval_score_hand_example():
    # band [1, 2], alpha 0.2 -> penalty 2/0.2 = 10 per unit outside.
    # y = 1.5 inside: 1. y = 0.5 below by 0.5: 1 + 5 = 6. y = 2.2 above by 0.2: 1 + 2 = 3. Mean = 10/3.
    assert M.interval_score([1.5, 0.5, 2.2], [1, 1, 1], [2, 2, 2], alpha=0.2) == pytest.approx(10 / 3, rel=1e-12)


def test_worse_forecast_gives_ratio_above_one_and_fails():
    rng = np.random.default_rng(0)
    y = rng.uniform(0.5, 2.0, 200)
    good, bad = y + rng.normal(0, 0.1, 200), y + rng.normal(0, 0.4, 200)
    r = M.mae_ratio_ci(y, bad, good, block=10, n_boot=2000, seed=1)
    assert r["ratio"] > 1 and r["ci_low"] > 1
    v = M.verdict(r["ratio"], r["ci_high"], 0.80, 0.95, 1.00, (0.75, 0.85))
    assert not v["pass"] and not v["mae_ratio_ok"]


def test_verdict_boundaries():
    rules = (0.95, 1.00, (0.75, 0.85))
    assert M.verdict(0.95, 0.99, 0.75, *rules)["pass"]  # every limit is inclusive except the CI's
    assert M.verdict(0.95, 0.99, 0.85, *rules)["pass"]
    assert not M.verdict(0.95, 1.00, 0.80, *rules)["pass"]  # CI upper bound must be strictly below 1
    assert not M.verdict(0.9501, 0.99, 0.80, *rules)["pass"]
    assert not M.verdict(0.90, 0.99, 0.7499, *rules)["pass"]
    assert not M.verdict(0.90, 0.99, 0.8501, *rules)["pass"]


def test_bootstrap_blocks_keep_neighbouring_days_together():
    idx = M.block_indices(n=95, block=10, n_boot=500, rng=np.random.default_rng(0))
    assert idx.shape == (500, 95)
    runs = idx[:, :90].reshape(500, 9, 10)  # the 9 full blocks of each resample
    assert (np.diff(runs, axis=2) == 1).all()  # consecutive days inside every block
    assert idx.min() == 0 and idx.max() == 94  # starts cover [0, n - block], so every day can be drawn
    assert (idx[:, 90:] - idx[:, 90:91] == np.arange(5)).all()  # the trimmed last block is a run too


def test_bootstrap_is_reproducible_and_paired():
    rng = np.random.default_rng(3)
    y, a, b = rng.uniform(1, 2, 120), rng.uniform(1, 2, 120), rng.uniform(1, 2, 120)
    r1 = M.mae_ratio_ci(y, a, b, 10, 1000, seed=9)
    assert r1 == M.mae_ratio_ci(y, a, b, 10, 1000, seed=9)
    assert r1["ci_low"] <= r1["ratio"] <= r1["ci_high"]
    same = M.mae_ratio_ci(y, a, a, 10, 1000, seed=9)
    assert same["ci_low"] == same["ci_high"] == 1.0  # paired: identical errors give ratio 1 in every resample


def test_block_bootstrap_is_wider_than_plain_when_errors_cluster():
    """Why D10: with clustered (autocorrelated) errors a plain bootstrap (block = 1) understates uncertainty."""
    rng = np.random.default_rng(4)
    n, phi = 200, 0.9
    z = np.zeros(n)
    for i in range(1, n):
        z[i] = phi * z[i - 1] + rng.normal()
    y = np.zeros(n)
    a, b = np.exp(0.5 * z), np.ones(n)  # method a's error comes in long good and bad stretches
    block = M.mae_ratio_ci(y, a, b, 10, 3000, seed=0)
    plain = M.mae_ratio_ci(y, a, b, 1, 3000, seed=0)
    assert block["ci_high"] - block["ci_low"] > 1.5 * (plain["ci_high"] - plain["ci_low"])


def test_closer_share_counts_ties_separately():
    out = M.closer_share([1.0, 1.0, 1.0], [1.0, 2.0, 0.5], [2.0, 1.0, 1.5])
    assert out == {"a_closer": pytest.approx(1 / 3), "ties": pytest.approx(1 / 3)}
