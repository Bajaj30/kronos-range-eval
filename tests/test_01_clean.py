import numpy as np
import pandas as pd
import pytest

from lib.bars import normalise
from lib.clean import DROP_ORDER, UnexpectedDefect, clean
from lib.features import add_target_and_baselines
from tests.helpers import assert_counts

TZ = "Asia/Kolkata"
PULL_DAY = pd.Timestamp("2025-01-17")
NAN = np.nan


def raw(rows):
    return pd.DataFrame({
        "Date": [f"{d} 00:00:00+05:30" for d, *_ in rows],
        "Open": [r[1] for r in rows], "High": [r[2] for r in rows],
        "Low": [r[3] for r in rows], "Close": [r[4] for r in rows], "Volume": [0] * len(rows),
    })


ROWS = [
    ("2025-01-06", 100, 102, 99, 100),
    ("2025-01-07", NAN, NAN, NAN, NAN),  # empty row (holiday placeholder) -> missing_price
    ("2025-01-08", 101, 103, 101, 102),  # its previous close must become 100 (Jan 6), not NaN
    ("2025-01-09", 102, 104, 101, 103),
    ("2025-01-10", 103, 103.2, 102.9, 103.1),  # Muhurat-style one-hour session -> dropped
    ("2025-01-13", 104, 106, 103, 105),  # previous close must become 103 (Jan 9)
    ("2025-01-14", 105, 105, 105, 105),  # flat bar -> impossible_bar
    ("2025-01-15", 105, 107, 104, 106),
    ("2025-01-17", 106, 108, 105, 107),  # pull day -> dropped first
]
MUHURAT = ["2025-01-10"]


def run(rows=ROWS):
    return clean(normalise(raw(rows), TZ), PULL_DAY, MUHURAT, spike_pct=20.0)


def test_each_reason_is_counted_exactly():
    _, dropped = run()
    assert_counts(dropped, {"pull_day_or_later": 1, "missing_price": 1, "muhurat_session": 1, "impossible_bar": 1})
    assert list(dropped) == DROP_ORDER


def test_previous_close_after_cleaning_is_the_last_kept_row():
    kept, _ = run()
    out = add_target_and_baselines(kept, atr_period=3).set_index("date")
    # Jan 8: H 103, L 101, prev close 100 (Jan 6) -> TR = 103 − 100 = 3 -> 3%.
    assert out.loc["2025-01-08", "tr_pct"] == pytest.approx(3.0)
    # Jan 13: H 106, L 103, prev close 103 (Jan 9, Muhurat dropped) -> TR = 106 − 103 = 3 -> 3/103.
    assert out.loc["2025-01-13", "tr_pct"] == pytest.approx(3 / 103 * 100)
    assert kept["date"].dt.strftime("%m-%d").tolist() == ["01-06", "01-08", "01-09", "01-13", "01-15"]


def test_wrong_order_would_give_a_different_answer():
    """Why order matters: computing first and dropping later leaves Jan 8 without a previous close."""
    computed_first = add_target_and_baselines(
        normalise(raw(ROWS), TZ).drop(columns=["ts_local"]), atr_period=3
    ).set_index("date")
    assert np.isnan(computed_first.loc["2025-01-08", "tr_pct"])


@pytest.mark.parametrize("bad, message", [
    (("2025-01-09", 102, 104, 101, 103), "duplicate_date"),  # same date twice
    (("2025-01-16", 150, 151, 149, 150), "price_spike"),  # +40% vs previous close
])
def test_never_seen_defects_stop_the_pipeline(bad, message):
    with pytest.raises(UnexpectedDefect, match=message):
        run(ROWS[:4] + [bad] + ROWS[4:])
