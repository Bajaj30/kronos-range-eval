"""Tuning and test windows (D3), with the ground-rule-2 checks in one place."""
import pandas as pd


def check_windows(release, tune_start, tune_end, test_start) -> None:
    release, tune_start, tune_end, test_start = map(pd.Timestamp, (release, tune_start, tune_end, test_start))
    if not release < tune_start:
        raise ValueError(f"tuning starts {tune_start.date()}, not after the model release {release.date()}")
    if not tune_start <= tune_end < test_start:
        raise ValueError("windows must be ordered tune_start <= tune_end < test_start (no overlap)")


def label_windows(dates: pd.Series, release, tune_start, tune_end, test_start) -> pd.Series:
    """'context' | 'tune' | 'test' per date. The test window is open-ended (to the last complete day)."""
    check_windows(release, tune_start, tune_end, test_start)
    d = pd.Series(pd.to_datetime(dates))
    labels = pd.Series("context", index=d.index)
    labels[(d >= pd.Timestamp(tune_start)) & (d <= pd.Timestamp(tune_end))] = "tune"
    labels[d >= pd.Timestamp(test_start)] = "test"
    return labels
