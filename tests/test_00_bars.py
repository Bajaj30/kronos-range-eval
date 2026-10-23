import numpy as np
import pandas as pd
import pytest

from lib.bars import DEFECTS, calendar_gaps, defect_counts, defect_masks, normalise
from tests.helpers import assert_counts

TZ = "Asia/Kolkata"
PULL_DAY = pd.Timestamp("2026-10-23")
NAN = np.nan


def raw_frame(rows):
    """rows: (date, open, high, low, close) -> a frame shaped like a Yahoo snapshot CSV read back."""
    return pd.DataFrame(
        {
            "Date": [f"{d} 00:00:00+05:30" for d, *_ in rows],
            "Open": [r[1] for r in rows],
            "High": [r[2] for r in rows],
            "Low": [r[3] for r in rows],
            "Close": [r[4] for r in rows],
            "Volume": [0] * len(rows),
        }
    )


CLEAN = [
    ("2025-01-06", 100, 105, 99, 104),
    ("2025-01-07", 104, 106, 103, 105),
    ("2025-01-08", 105, 107, 104, 106),
    ("2025-01-09", 106, 108, 105, 107),
    ("2025-01-10", 107, 109, 106, 108),
]

# 10 hand-made rows with exactly: 1 duplicate date, 1 flat bar, 1 broken high, 1 missing close.
SEEDED = [
    ("2025-01-06", 100, 105, 99, 104),  # clean
    ("2025-01-07", 104, 106, 103, 105),  # clean
    ("2025-01-07", 104, 106, 103, 105),  # duplicate_date
    ("2025-01-08", 105, 105, 105, 105),  # flat_bar
    ("2025-01-09", 105, 104, 103, 104),  # high_below_body (high 104 < open 105)
    ("2025-01-10", 104, 106, 103, NAN),  # missing_price
    ("2025-01-13", 104, 107, 103, 106),  # clean
    ("2025-01-14", 106, 108, 105, 107),  # clean
    ("2025-01-15", 107, 109, 106, 108),  # clean
    ("2025-01-16", 108, 110, 107, 109),  # clean
]
SEEDED_EXPECTED = {name: 0 for name in DEFECTS} | {
    "duplicate_date": 1,
    "flat_bar": 1,
    "high_below_body": 1,
    "missing_price": 1,
}


def counts(rows, pull_day=PULL_DAY):
    return defect_counts(normalise(raw_frame(rows), TZ), pull_day, spike_pct=20.0)


def test_clean_rows_have_no_defects():
    assert_counts(counts(CLEAN), {name: 0 for name in DEFECTS})


def test_seeded_rows_give_exact_counts():
    assert_counts(counts(SEEDED), SEEDED_EXPECTED)


def test_the_tester_fails_on_a_wrong_count():
    wrong = SEEDED_EXPECTED | {"flat_bar": 2}
    with pytest.raises(AssertionError):
        assert_counts(counts(SEEDED), wrong)


def test_the_tester_fails_on_a_missing_key():
    incomplete = {k: v for k, v in SEEDED_EXPECTED.items() if k != "price_spike"}
    with pytest.raises(AssertionError):
        assert_counts(counts(SEEDED), incomplete)


@pytest.mark.parametrize(
    "defect, row_index, bad_row, also",
    [
        ("low_above_body", 2, ("2025-01-08", 105, 107, 105.5, 106), set()),
        # A zero price is necessarily >20% from the previous close, so it is also a spike.
        ("nonpositive_price", 2, ("2025-01-08", 105, 107, 0, 106), {"price_spike"}),
        # +23.8% vs previous close 105; the next row (low 105 vs close 130) is -19.2%, just under the threshold.
        ("price_spike", 2, ("2025-01-08", 130, 131, 129, 130), set()),
        ("out_of_order", 2, ("2025-01-03", 105, 107, 104, 106), set()),
        ("on_or_after_pull_day", 4, ("2026-10-23", 107, 109, 106, 108), set()),
    ],
)
def test_each_defect_is_found_on_its_row_only(defect, row_index, bad_row, also):
    rows = list(CLEAN)
    rows[row_index] = bad_row
    masks = defect_masks(normalise(raw_frame(rows), TZ), PULL_DAY, spike_pct=20.0)
    expected_rows = [i == row_index for i in range(len(rows))]
    for name, mask in masks.items():
        expected = expected_rows if name in {defect} | also else [False] * len(rows)
        assert mask.tolist() == expected, name


def test_not_midnight_flags_intraday_timestamp():
    raw = raw_frame(CLEAN)
    raw.loc[1, "Date"] = "2025-01-07 09:15:00+05:30"
    masks = defect_masks(normalise(raw, TZ), PULL_DAY, spike_pct=20.0)
    assert masks["not_midnight"].tolist() == [False, True, False, False, False]


def test_normalise_keeps_ist_date_from_utc_timestamp():
    # 2025-01-06 00:00 IST is 2025-01-05 18:30 UTC; the market date must stay the 6th.
    raw = raw_frame(CLEAN[:1])
    raw.loc[0, "Date"] = "2025-01-05 18:30:00+00:00"
    assert normalise(raw, TZ)["date"].iloc[0] == pd.Timestamp("2025-01-06")


def test_calendar_gaps_threshold():
    dates = pd.Series(pd.to_datetime(["2025-01-03", "2025-01-06", "2025-01-11", "2025-01-17"]))
    gaps = calendar_gaps(dates, min_days=5)
    # Fri->Mon is 3 days (no gap), Mon->Sat is 5 days (not more than 5), Sat->Fri is 6 days (gap).
    assert gaps["days"].tolist() == [6]
    assert gaps["to"].iloc[0] == pd.Timestamp("2025-01-17")
