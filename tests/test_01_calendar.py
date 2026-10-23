import json

import pandas as pd
import pytest

from lib.nse_calendar import expected_sessions, load_holidays, reconcile, scorable_mask
from lib.windows import check_windows, label_windows

# Two made-up weeks: Mon 2025-03-03 .. Fri 2025-03-14.
HOLIDAYS = ["2025-03-05"]  # Wed, week 1
MUHURAT = ["2025-03-13"]  # Thu, week 2: one-hour session, not a regular bar
FULL = ["2025-03-08"]  # Sat, week 1: full special session
EXPECTED = expected_sessions("2025-03-03", "2025-03-14", HOLIDAYS, FULL, MUHURAT)


def d(*days):
    return [pd.Timestamp(f"2025-03-{x:02d}") for x in days]


def test_expected_sessions():
    assert list(EXPECTED) == d(3, 4, 6, 7, 8, 10, 11, 12, 14)


def test_reconcile_finds_exactly_the_missing_and_the_extra():
    data = d(3, 4, 5, 6, 7, 10, 11, 12, 14)  # no Saturday 8th; an extra row on the 5th (a holiday)
    missing, extra = reconcile(data, EXPECTED, "2025-03-03", "2025-03-14")
    assert (missing, extra) == (d(8), d(5))


def test_scorable_rules():
    data = pd.Series(d(3, 4, 6, 7, 10, 11, 12, 14))  # Saturday 8th missing from the data
    ok = dict(zip(data, scorable_mask(data, EXPECTED)))
    assert not ok[pd.Timestamp("2025-03-03")]  # first session: no predecessor
    assert ok[pd.Timestamp("2025-03-06")]  # after a holiday: previous session is the 4th, present
    assert not ok[pd.Timestamp("2025-03-10")]  # previous session (Sat 8th) is missing from the data
    assert ok[pd.Timestamp("2025-03-11")]
    assert ok[pd.Timestamp("2025-03-14")]  # after the Muhurat day: previous regular session is the 12th
    assert int(scorable_mask(data, EXPECTED).sum()) == 6


def test_extra_row_makes_the_next_day_unscorable():
    data = pd.Series(d(3, 4, 5, 6))  # a row on the 5th (holiday) sits between the 4th and the 6th
    assert scorable_mask(data, EXPECTED).tolist() == [False, True, False, False]


def test_holiday_list_with_a_session_is_refused(tmp_path):
    doc = {"holidays": [{"date": "2024-03-02", "weekday": "Saturday", "description": "Special Live Trading"}]}
    (tmp_path / "nse_holidays_2024.json").write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="sessions"):
        load_holidays(tmp_path, [2024])


def test_windows_labels_and_guards():
    dates = pd.Series(pd.to_datetime(["2025-08-29", "2025-09-01", "2025-12-31", "2026-01-02"]))
    labels = label_windows(dates, "2025-08-02", "2025-09-01", "2025-12-31", "2026-01-01")
    assert labels.tolist() == ["context", "tune", "tune", "test"]
    with pytest.raises(ValueError, match="release"):
        check_windows("2025-08-02", "2025-07-01", "2025-12-31", "2026-01-01")
    with pytest.raises(ValueError, match="overlap"):
        check_windows("2025-08-02", "2025-09-01", "2026-01-15", "2026-01-01")
