"""Step 00b: look at the raw snapshot before trusting it (playbook 1.6).

Counts every kind of bad bar, gaps, volume quality and cross-index date mismatches, writes them to
out/facts/00_data.json (rendered into FACTS.md), and prints real rows to read by eye. Changes no data.
"""
import pandas as pd

import config
from lib import facts as F
from lib.bars import DEFECTS, calendar_gaps, defect_masks, normalise
from lib.snapshot import load_raw, verify_snapshot

SNAP = config.RAW_DIR / config.SNAPSHOT_ID


def profile(name: str, pull_day: pd.Timestamp):
    raw = load_raw(SNAP, name)
    df = normalise(raw, config.MARKET_TZ)
    masks = defect_masks(df, pull_day, config.SPIKE_PCT)
    any_defect = pd.concat(masks, axis=1).any(axis=1)
    g = f"RAW-{name}"

    vol = df["volume"]
    positive = vol > 0
    gaps = calendar_gaps(df["date"], config.GAP_DAYS)
    weekend = df[df["date"].dt.day_of_week >= 5]
    # NaN-aware: on a missing-price row NaN != NaN is True, which once made every such row look like a mismatch.
    both = raw["Adj Close"].notna() & raw["Close"].notna()
    adj_rel = ((raw["Adj Close"] - raw["Close"]).abs() / raw["Close"])[both]
    extra_cols = {
        "adj_close_max_rel_diff": float(adj_rel.max()),
        "dividend_rows": int((raw["Dividends"] != 0).sum()),
        "split_rows": int((raw["Stock Splits"] != 0).sum()),
    }

    rows = [
        F.fact("rows", len(df), g, "rows as received"),
        F.fact("first_date", str(df["date"].min().date()), g, "first bar date"),
        F.fact("last_date", str(df["date"].max().date()), g, "last bar date"),
    ]
    rows += [F.fact(f"defect_{d}", int(masks[d].sum()), g, f"rows flagged {d}") for d in DEFECTS]
    rows += [
        F.fact("rows_with_any_defect", int(any_defect.sum()), g, "rows with at least one defect"),
        F.fact("rows_without_defect", int((~any_defect).sum()), g, "rows with no defect"),
        F.fact("gaps_over_threshold", len(gaps), g, f"consecutive rows more than {config.GAP_DAYS} calendar days apart"),
        F.fact("weekend_rows", len(weekend), g, "rows dated Saturday or Sunday (special sessions?)"),
        F.fact("volume_zero_rows", int((vol == 0).sum()), g, "rows with volume exactly 0"),
        F.fact("volume_nan_rows", int(vol.isna().sum()), g, "rows with volume missing"),
        F.fact("volume_positive_rows", int(positive.sum()), g, "rows with volume > 0"),
        F.fact("volume_first_positive", str(df.loc[positive, "date"].min().date()), g, "first date with volume > 0"),
        F.fact("volume_last_zero", str(df.loc[vol == 0, "date"].max().date()) if (vol == 0).any() else "none", g,
               "last date with volume 0"),
    ]
    rows += [F.fact(k, v, g, desc) for (k, v), desc in zip(extra_cols.items(), [
        "largest |Adj Close - Close| / Close where both exist (Adj Close is not used)",
        "rows with a non-zero dividend (expected 0)",
        "rows with a non-zero split (expected 0)",
    ])]

    by_year = df.assign(year=df["date"].dt.year, zero_vol=(vol == 0)).groupby("year").agg(
        rows=("date", "size"), zero_volume=("zero_vol", "sum"))
    tables = [
        {"title": f"{name}: rows per calendar year", "group": g, "columns": ["year", "rows", "zero-volume rows"],
         "rows": [[int(y), int(r.rows), int(r.zero_volume)] for y, r in by_year.iterrows()]},
    ]
    if len(gaps):
        tables.append({"title": f"{name}: gaps over {config.GAP_DAYS} calendar days", "group": g,
                       "columns": ["from", "to", "days"],
                       "rows": [[str(r["from"].date()), str(r["to"].date()), int(r["days"])] for _, r in gaps.iterrows()]})
    # Lowest-volume real rows: special short sessions (e.g. the one-hour Diwali Muhurat session) show up here.
    low_vol = df[positive & ~any_defect].nsmallest(10, "volume").sort_values("date")
    tables.append({"title": f"{name}: 10 lowest-volume rows (volume > 0, no defect)", "group": g,
                   "columns": ["date", "weekday", "volume", "(high-low)/open %"],
                   "rows": [[str(r.date.date()), r.date.day_name()[:3], int(r.volume),
                             round((r.high - r.low) / r.open * 100, 2)] for _, r in low_vol.iterrows()]})
    flagged = df[any_defect | (df["date"].dt.day_of_week >= 5)]
    if len(flagged):
        reasons = pd.concat(masks, axis=1)
        tables.append({"title": f"{name}: every flagged or weekend row", "group": g,
                       "columns": ["date", "weekday", "defects"],
                       "rows": [[str(r.date.date()), r.date.day_name()[:3],
                                 ", ".join(d for d in DEFECTS if reasons.loc[i, d]) or "weekend only"]
                                for i, r in flagged.iterrows()]})
    return df, rows, tables


def show(name: str, df: pd.DataFrame):
    """Print real rows to read by eye. Console only: raw data stays out of git (D19)."""
    view = df.assign(wd=df["date"].dt.day_name().str[:3],
                     hl_pct=(df["high"] - df["low"]) / df["open"] * 100)[
        ["date", "wd", "open", "high", "low", "close", "volume", "hl_pct"]]
    pd.set_option("display.width", 140)
    print(f"\n===== {name}: 20 real rows (first 5, 10 random, last 5) =====")
    sample = pd.concat([view.head(5), view.iloc[5:-5].sample(10, random_state=0).sort_index(), view.tail(5)])
    print(sample.to_string(float_format=lambda x: f"{x:,.2f}"))
    print(f"\n----- {name}: 8 smallest and 8 largest (high-low)/open % -----")
    ranked = view.dropna(subset=["hl_pct"]).sort_values("hl_pct")
    print(pd.concat([ranked.head(8), ranked.tail(8)]).to_string(float_format=lambda x: f"{x:,.2f}"))


def main():
    manifest = verify_snapshot(SNAP)
    pull_day = pd.Timestamp(manifest["created_utc"]).tz_convert(config.MARKET_TZ).tz_localize(None).normalize()

    groups = {
        "SNAPSHOT": f"snapshot {config.SNAPSHOT_ID} as a whole",
        **{f"RAW-{n}": f"{n} ({s}) daily rows exactly as received in snapshot {config.SNAPSHOT_ID}"
           for n, s in config.TICKERS.items()},
    }
    all_facts = [
        F.fact("snapshot_id", manifest["snapshot_id"], "SNAPSHOT", "snapshot id"),
        F.fact("created_utc", manifest["created_utc"], "SNAPSHOT", "when the pull finished (UTC)"),
        F.fact("pull_day_ist", str(pull_day.date()), "SNAPSHOT", "pull date in market time; bars on this date may be unfinished"),
        F.fact("yfinance_version", manifest["yfinance_version"], "SNAPSHOT", "yfinance version used for the pull"),
    ]
    all_facts += [F.fact(f"sha256_{n}", f["sha256"], "SNAPSHOT", f"sha256 of {f['file']}") for n, f in manifest["files"].items()]
    all_tables, frames = [], {}
    for name in config.TICKERS:
        df, rows, tables = profile(name, pull_day)
        frames[name] = df
        all_facts += rows
        all_tables += tables

    names = list(config.TICKERS)
    a, b = (set(frames[n]["date"]) for n in names)
    only_a, only_b = sorted(a - b), sorted(b - a)
    all_facts += [
        F.fact(f"dates_only_in_{names[0]}", len(only_a), "SNAPSHOT", f"dates present in {names[0]} but not {names[1]}"),
        F.fact(f"dates_only_in_{names[1]}", len(only_b), "SNAPSHOT", f"dates present in {names[1]} but not {names[0]}"),
    ]
    if only_a or only_b:
        all_tables.append({"title": "Dates present in only one index", "group": "SNAPSHOT", "columns": ["date", "only in"],
                           "rows": [[str(d.date()), names[0]] for d in only_a] + [[str(d.date()), names[1]] for d in only_b]})

    path = F.write_step(config.FACTS_DIR, "00", "Raw data profile", "00b_profile.py", groups, all_facts, all_tables)
    print(f"wrote {path.relative_to(config.ROOT)}: {len(all_facts)} facts, {len(all_tables)} tables")
    for name in names:
        show(name, frames[name])


if __name__ == "__main__":
    main()
