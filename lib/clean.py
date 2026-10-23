"""Cleaning in a fixed order (Chunk 1, P3).

Rows are removed BEFORE anything that looks at "the previous row" (true range, ATR) is computed:
removing a row changes which close counts as the previous one.
"""
import pandas as pd

from lib.bars import defect_counts, defect_masks

# Removed, in this order, and counted by reason.
DROP_ORDER = ["pull_day_or_later", "missing_price", "muhurat_session", "impossible_bar"]
IMPOSSIBLE = ["flat_bar", "high_below_body", "low_above_body", "nonpositive_price"]
# Never seen in the data so far: if one appears, stop for a human look instead of guessing a fix.
STOP_ON = ["duplicate_date", "out_of_order", "not_midnight", "price_spike"]


class UnexpectedDefect(RuntimeError):
    pass


def clean(df: pd.DataFrame, pull_day, muhurat_dates, spike_pct: float) -> tuple[pd.DataFrame, dict[str, int]]:
    """Normalised bars (lib.bars.normalise) -> (clean bars, rows dropped per reason in DROP_ORDER)."""
    masks = defect_masks(df, pull_day, spike_pct)
    seen = {d: int(masks[d].sum()) for d in STOP_ON if masks[d].any()}
    if seen:
        raise UnexpectedDefect(f"defects never handled before, inspect the data: {seen}")

    muhurat = set(pd.to_datetime(list(muhurat_dates)))
    steps = {
        "pull_day_or_later": lambda d: defect_masks(d, pull_day, spike_pct)["on_or_after_pull_day"],
        "missing_price": lambda d: defect_masks(d, pull_day, spike_pct)["missing_price"],
        "muhurat_session": lambda d: d["date"].isin(muhurat),
        "impossible_bar": lambda d: pd.concat([defect_masks(d, pull_day, spike_pct)[k] for k in IMPOSSIBLE], axis=1).any(axis=1),
    }
    assert list(steps) == DROP_ORDER
    out, dropped = df.reset_index(drop=True), {}
    for reason, find in steps.items():
        hit = find(out)
        dropped[reason] = int(hit.sum())
        out = out[~hit].reset_index(drop=True)

    remaining = {k: v for k, v in defect_counts(out, pull_day, spike_pct).items() if v}
    if remaining:
        raise UnexpectedDefect(f"defects remain after cleaning: {remaining}")
    return out, dropped
