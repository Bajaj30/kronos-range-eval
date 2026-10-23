"""The target and the simple baselines, each defined once (ground rule 5).

Input: cleaned bars in date order (lib.clean). All columns are in % of the previous close C(t-1),
which is known before day t starts.
  tr_pct          target: true range of day t
  atr_prev_pct    ATR(14) forecast: Wilder ATR in points through day t-1, divided by C(t-1)
  naive_prev_pct  "tomorrow = today": the true range of day t-1
"""
import numpy as np
import pandas as pd


def true_range(df: pd.DataFrame) -> pd.Series:
    """max(H_t, C_t-1) − min(L_t, C_t-1) in points; NaN on the first row (no previous close)."""
    prev_close = df["close"].shift(1)
    return pd.concat([df["high"], prev_close], axis=1).max(axis=1, skipna=False) - pd.concat(
        [df["low"], prev_close], axis=1
    ).min(axis=1, skipna=False)


def wilder_atr(tr: pd.Series, n: int) -> pd.Series:
    """Wilder's ATR: seed = mean of the first n true ranges, then ATR_t = ATR_t-1 + (TR_t − ATR_t-1) / n.

    ATR on row t includes day t; callers shift it by one row to get a forecast.
    """
    v = tr.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    valid = np.flatnonzero(~np.isnan(v))
    if len(valid) >= n:
        start = valid[0]
        if np.isnan(v[start:]).any():
            raise ValueError("true range has a gap after its first value; clean the rows first")
        seed = start + n - 1
        out[seed] = v[start : seed + 1].mean()
        for i in range(seed + 1, len(v)):
            out[i] = out[i - 1] + (v[i] - out[i - 1]) / n
    return pd.Series(out, index=tr.index)


def add_target_and_baselines(df: pd.DataFrame, atr_period: int) -> pd.DataFrame:
    if not df["date"].is_monotonic_increasing or df["date"].duplicated().any():
        raise ValueError("bars must be cleaned and in strictly increasing date order")
    out = df.copy()
    prev_close = out["close"].shift(1)
    tr = true_range(out)
    out["tr_pct"] = tr / prev_close * 100
    out["atr_prev_pct"] = wilder_atr(tr, atr_period).shift(1) / prev_close * 100
    out["naive_prev_pct"] = out["tr_pct"].shift(1)
    return out
