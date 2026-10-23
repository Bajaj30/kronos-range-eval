"""Daily OHLC bars: normalise raw Yahoo rows and find bad bars.

Chunk 0 counts the defects; Chunk 1 removes them with these same functions (ground rule 5).
"""
import pandas as pd

PRICE_COLS = ["open", "high", "low", "close"]

# Order is fixed so every report lists defects the same way.
DEFECTS = [
    "missing_price",  # any of O/H/L/C is NaN
    "duplicate_date",  # a later row with a date already seen (the first copy is not counted)
    "out_of_order",  # date earlier than the previous row's date
    "flat_bar",  # high == low: usually a holiday or placeholder row, which would fake a zero range
    "high_below_body",  # high < max(open, close): impossible bar
    "low_above_body",  # low > min(open, close): impossible bar
    "nonpositive_price",  # any price <= 0
    "price_spike",  # any O/H/L/C more than spike_pct % away from the previous row's close
    "not_midnight",  # timestamp is not 00:00 market time, so it may not be a daily bar
    "on_or_after_pull_day",  # dated on the pull day or later: possibly an unfinished bar
]


def normalise(raw: pd.DataFrame, tz: str) -> pd.DataFrame:
    """Raw Yahoo frame (as read from the snapshot CSV) -> date, ts_local, open, high, low, close, volume.

    Keeps every row, in the original order: removing rows is cleaning, which is Chunk 1's job.
    """
    ts = pd.to_datetime(raw["Date"], utc=True).dt.tz_convert(tz)
    out = pd.DataFrame({"ts_local": ts, "date": ts.dt.tz_localize(None).dt.normalize()})
    for col in PRICE_COLS:
        out[col] = pd.to_numeric(raw[col.capitalize()], errors="coerce").astype(float)
    out["volume"] = pd.to_numeric(raw["Volume"], errors="coerce").astype(float)
    return out


def defect_masks(df: pd.DataFrame, pull_day: pd.Timestamp, spike_pct: float) -> dict[str, pd.Series]:
    """One boolean Series per defect in DEFECTS. A row can carry several defects.

    NaN comparisons are False, and max/min use skipna=False, so a missing price is counted only
    as missing_price and not also as an impossible bar.
    """
    prices = df[PRICE_COLS]
    body_max = df[["open", "close"]].max(axis=1, skipna=False)
    body_min = df[["open", "close"]].min(axis=1, skipna=False)
    prev_close = df["close"].shift(1)
    deviation_pct = prices.sub(prev_close, axis=0).abs().div(prev_close, axis=0) * 100

    masks = {
        "missing_price": prices.isna().any(axis=1),
        "duplicate_date": df["date"].duplicated(keep="first"),
        "out_of_order": df["date"] < df["date"].shift(1),
        "flat_bar": df["high"] == df["low"],
        "high_below_body": df["high"] < body_max,
        "low_above_body": df["low"] > body_min,
        "nonpositive_price": (prices <= 0).any(axis=1),
        "price_spike": (deviation_pct > spike_pct).any(axis=1),
        "not_midnight": df["ts_local"] != df["ts_local"].dt.normalize(),
        "on_or_after_pull_day": df["date"] >= pd.Timestamp(pull_day).normalize(),
    }
    assert list(masks) == DEFECTS
    return masks


def defect_counts(df: pd.DataFrame, pull_day: pd.Timestamp, spike_pct: float) -> dict[str, int]:
    return {name: int(mask.sum()) for name, mask in defect_masks(df, pull_day, spike_pct).items()}


def calendar_gaps(dates: pd.Series, min_days: int) -> pd.DataFrame:
    """Consecutive rows more than min_days calendar days apart (dates assumed sorted)."""
    d = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    days = d.diff().dt.days
    hit = days > min_days
    return pd.DataFrame({"from": d.shift(1)[hit], "to": d[hit], "days": days[hit].astype(int)}).reset_index(drop=True)
