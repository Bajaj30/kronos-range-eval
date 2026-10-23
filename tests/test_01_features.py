import numpy as np
import pandas as pd
import pytest

from lib.features import add_target_and_baselines, true_range, wilder_atr


def bars(rows):
    """rows: (date, open, high, low, close)."""
    return pd.DataFrame(rows, columns=["date", "open", "high", "low", "close"]).assign(
        date=lambda d: pd.to_datetime(d["date"])
    )


# Real NIFTY rows (Yahoo, 2015 — far from the tuning and test windows). Expected TR% values were
# computed separately with exact decimal arithmetic, not with the code under test:
#   2015-01-05 prev close inside the range: TR = H − L         = 81.69921875     -> 0.97313684018536...%
#   2015-01-06 gap down, prev close above H: TR = C_prev − L    = 267.05029296875 -> 3.18736609040032...%
#   2015-01-08 gap up, prev close below L:   TR = H − C_prev    = 141.39990234375 -> 1.74522531984829...%
REAL = bars([
    ("2015-01-02", 8288.7001953125, 8410.599609375, 8288.7001953125, 8395.4501953125),
    ("2015-01-05", 8407.9501953125, 8445.599609375, 8363.900390625, 8378.400390625),
    ("2015-01-06", 8325.2998046875, 8327.849609375, 8111.35009765625, 8127.35009765625),
    ("2015-01-07", 8118.64990234375, 8151.2001953125, 8065.4501953125, 8102.10009765625),
    ("2015-01-08", 8191.39990234375, 8243.5, 8167.2998046875, 8234.599609375),
])
HAND_TR_PCT = {1: 0.973136840185363607, 2: 3.18736609040032953, 4: 1.74522531984829117}


def test_true_range_pct_matches_hand_calculation():
    out = add_target_and_baselines(REAL, atr_period=3)
    for row, expected in HAND_TR_PCT.items():
        assert out["tr_pct"].iloc[row] == pytest.approx(expected, rel=1e-12), row
    assert np.isnan(out["tr_pct"].iloc[0])  # no previous close on the first row


def test_the_tester_fails_on_a_wrong_hand_value():
    out = add_target_and_baselines(REAL, atr_period=3)
    with pytest.raises(AssertionError):
        assert out["tr_pct"].iloc[2] == pytest.approx(3.1873, rel=1e-12)  # right to 4 digits, wrong at 1e-12


def test_wilder_atr_hand_example():
    # n = 3, TR = [NaN, 3, 6, 9, 3]: seed on row 3 = mean(3, 6, 9) = 6; row 4 = 6 + (3 − 6) / 3 = 5.
    atr = wilder_atr(pd.Series([np.nan, 3.0, 6.0, 9.0, 3.0]), n=3)
    assert np.isnan(atr.iloc[:3]).all()
    assert atr.iloc[3:].tolist() == [6.0, 5.0]


def test_wilder_atr_refuses_a_gap():
    with pytest.raises(ValueError, match="gap"):
        wilder_atr(pd.Series([np.nan, 3.0, np.nan, 9.0, 3.0]), n=2)


def synthetic(n=40, seed=0):
    rng = np.random.default_rng(seed)
    close = 20000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.01, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.01, n))
    return pd.DataFrame({"date": pd.bdate_range("2025-01-01", periods=n), "open": open_, "high": high,
                         "low": low, "close": close})


def test_perturbing_day_t_changes_only_day_t_and_later():
    """Multiply day t's high by 5. The forecast for day t must not move; the target and t+1's forecasts must."""
    t = 30
    base = add_target_and_baselines(synthetic(), atr_period=14)
    bumped_bars = synthetic()
    bumped_bars.loc[t, "high"] *= 5
    bumped = add_target_and_baselines(bumped_bars, atr_period=14)

    assert bumped["atr_prev_pct"].iloc[t] == base["atr_prev_pct"].iloc[t]  # no future in the forecast
    assert bumped["naive_prev_pct"].iloc[t] == base["naive_prev_pct"].iloc[t]
    assert bumped["tr_pct"].iloc[t] != base["tr_pct"].iloc[t]  # the target sees its own day
    # ...and the bump is not ignored: tomorrow's forecasts use it (a function ignoring highs would fail here).
    assert bumped["atr_prev_pct"].iloc[t + 1] > base["atr_prev_pct"].iloc[t + 1]
    assert bumped["naive_prev_pct"].iloc[t + 1] > base["naive_prev_pct"].iloc[t + 1]
    pd.testing.assert_frame_equal(bumped.iloc[:t, :], base.iloc[:t, :].assign(high=bumped["high"].iloc[:t]))


def test_atr_prev_is_yesterdays_atr_over_yesterdays_close():
    df = synthetic()
    out = add_target_and_baselines(df, atr_period=14)
    atr_points = wilder_atr(true_range(df), 14)
    t = 25
    assert out["atr_prev_pct"].iloc[t] == pytest.approx(atr_points.iloc[t - 1] / df["close"].iloc[t - 1] * 100)


def test_unsorted_input_is_refused():
    with pytest.raises(ValueError, match="increasing"):
        add_target_and_baselines(REAL.iloc[::-1].reset_index(drop=True), atr_period=3)


def test_atr_matches_the_ta_library_once_the_seed_has_faded():
    """Independent implementation check. The libraries seed differently (ta includes row 0's high − low),
    so early rows differ; after ~300 rows the seed's weight (13/14)^300 is ~2e-10 and they must agree."""
    from ta.volatility import AverageTrueRange

    df = synthetic(n=400, seed=1)
    ours = wilder_atr(true_range(df), 14)
    theirs = AverageTrueRange(df["high"], df["low"], df["close"], window=14, fillna=False).average_true_range()
    assert ((ours - theirs).abs() / theirs).iloc[300:].max() < 1e-8
