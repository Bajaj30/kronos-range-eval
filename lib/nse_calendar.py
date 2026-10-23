"""NSE session calendar: which dates should have a regular daily bar, and which bars can be scored.

Sources (all in data/calendar/, committed):
  nse_holidays_<year>.json   official NSE F&O holiday list (tools/fetch_nse_holidays.py)
  special_sessions.csv       full sessions on non-trading days (e.g. Budget Sunday), with sources
  muhurat_sessions.csv       one-hour Diwali sessions; their rows are dropped (D21)
"""
import json
from pathlib import Path

import pandas as pd


def load_holidays(calendar_dir, years) -> pd.DataFrame:
    """date, description. Refuses entries that are sessions, not holidays (NSE's 2024 list had one)."""
    rows = []
    for year in years:
        rows += json.loads((Path(calendar_dir) / f"nse_holidays_{year}.json").read_text())["holidays"]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    sessions = df[df["description"].str.contains("live trading", case=False)]
    if len(sessions):
        raise ValueError(f"holiday list contains sessions, decide how to treat them: {sessions.to_dict('records')}")
    return df[["date", "description"]]


def load_dated_csv(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    if df["date"].duplicated().any():
        raise ValueError(f"{Path(path).name}: duplicate dates")
    return df


def expected_sessions(start, end, holidays, full_sessions, muhurat) -> pd.DatetimeIndex:
    """Dates that should carry a regular daily bar: weekdays − holidays − Muhurat days + full special sessions."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    skip = set(pd.to_datetime(list(holidays))) | set(pd.to_datetime(list(muhurat)))
    regular = {d for d in pd.bdate_range(start, end) if d not in skip}
    extra = {d for d in pd.to_datetime(list(full_sessions)) if start <= d <= end}
    return pd.DatetimeIndex(sorted(regular | extra))


def reconcile(data_dates, expected: pd.DatetimeIndex, start, end) -> tuple[list, list]:
    """(expected sessions missing from the data, data rows on dates that are not sessions), within [start, end]."""
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    have = {d for d in pd.to_datetime(list(data_dates)) if start <= d <= end}
    want = set(expected)
    return sorted(want - have), sorted(have - want)


def scorable_mask(dates: pd.Series, expected: pd.DatetimeIndex) -> pd.Series:
    """True where day t is a session AND the data's previous row is the session just before t.

    That is exactly when "previous close" in the true range means the previous session's close.
    It is False after a session missing from the data, and for the calendar's first session.
    """
    dates = pd.Series(pd.to_datetime(dates)).reset_index(drop=True)
    if not dates.is_monotonic_increasing:
        raise ValueError("dates must be sorted")
    prev_session = dict(zip(expected[1:], expected[:-1]))
    expected_prev = dates.map(prev_session)
    return dates.isin(expected) & expected_prev.notna() & (dates.shift(1) == expected_prev)
