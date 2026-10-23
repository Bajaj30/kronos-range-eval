"""Step 01: clean the raw bars, check them against the official NSE calendar, compute the target and baselines.

Writes data/clean/<snapshot>/<INDEX>.csv + manifest (not in git, D19) and out/facts/01.json.
Columns: date, open, high, low, close, tr_pct, atr_prev_pct, naive_prev_pct, window, scorable.
Looks only at counts and dates in the test window, never at outcomes (no peeking before PREREG).
"""
import json

import pandas as pd
from ta.volatility import AverageTrueRange

import config
from lib import facts as F
from lib.bars import normalise
from lib.clean import DROP_ORDER, clean
from lib.features import add_target_and_baselines
from lib.nse_calendar import expected_sessions, load_dated_csv, load_holidays, reconcile, scorable_mask
from lib.snapshot import load_raw, sha256_file, verify_snapshot, write_derived
from lib.windows import label_windows

SNAP = config.RAW_DIR / config.SNAPSHOT_ID
OUT_COLS = ["date", "open", "high", "low", "close", "tr_pct", "atr_prev_pct", "naive_prev_pct", "window", "scorable"]


def check_muhurat_closes(nifty_raw: pd.DataFrame, muhurat: pd.DataFrame) -> list[list]:
    """Each Muhurat date with a NIFTY row must carry the published Muhurat close: proves the dates are right."""
    by_date = nifty_raw.set_index("date")["close"]
    rows = []
    for _, m in muhurat.iterrows():
        yahoo = by_date.get(m["date"])
        published = m["nifty_close_published"]
        if yahoo is None or pd.isna(yahoo) or pd.isna(published):
            rows.append([str(m["date"].date()), f"{published:.2f}" if pd.notna(published) else "—", "no row or no price", "n/a"])
            continue
        match = abs(yahoo - published) <= 0.01
        if not match:
            raise AssertionError(f"Muhurat {m['date'].date()}: Yahoo close {yahoo} != published {published}")
        rows.append([str(m["date"].date()), f"{published:.2f}", f"{yahoo:.2f}", "yes"])  # text: keep the paisa
    return rows


def main():
    manifest = verify_snapshot(SNAP)
    pull_day = pd.Timestamp(manifest["created_utc"]).tz_convert(config.MARKET_TZ).tz_localize(None).normalize()
    last_complete = pull_day - pd.Timedelta(days=1)

    holidays = load_holidays(config.CALENDAR_DIR, config.HOLIDAY_YEARS)
    specials = load_dated_csv(config.CALENDAR_DIR / "special_sessions.csv")
    muhurat = load_dated_csv(config.CALENDAR_DIR / "muhurat_sessions.csv")
    expected = expected_sessions(config.CALENDAR_START, last_complete, holidays["date"], specials["date"], muhurat["date"])

    raw = {name: normalise(load_raw(SNAP, name), config.MARKET_TZ) for name in config.TICKERS}
    muhurat_table = check_muhurat_closes(raw["NIFTY"], muhurat)

    groups = {"CALENDAR": f"official NSE session calendar check, {config.CALENDAR_START} to {last_complete.date()}"}
    facts = [
        F.fact("expected_sessions", len(expected), "CALENDAR", "sessions that should have a daily bar"),
        F.fact("muhurat_dates_listed", len(muhurat), "CALENDAR", "Muhurat dates in muhurat_sessions.csv"),
        F.fact("muhurat_closes_matched", sum(r[3] == "yes" for r in muhurat_table), "CALENDAR",
               "Muhurat dates whose NIFTY row equals the published Muhurat close"),
    ]
    tables = [{"title": "Muhurat dates checked against published closes", "group": "CALENDAR",
               "columns": ["date", "published NIFTY close", "Yahoo close", "match"], "rows": muhurat_table}]

    frames = {}
    for name in config.TICKERS:
        kept, dropped = clean(raw[name], pull_day, muhurat["date"], config.SPIKE_PCT)
        missing, extra = reconcile(kept["date"], expected, config.CALENDAR_START, last_complete)
        if extra:
            raise AssertionError(f"{name}: rows on non-session days {extra}; update the calendar or the data")

        out = add_target_and_baselines(kept, config.ATR_PERIOD)
        out["window"] = label_windows(out["date"], config.KRONOS_RELEASE, config.TUNE_START, config.TUNE_END,
                                      config.TEST_START)
        has_values = out[["tr_pct", "atr_prev_pct", "naive_prev_pct"]].notna().all(axis=1)
        out["scorable"] = scorable_mask(out["date"], expected) & has_values

        # Self-checks on the real data (playbook 6.2).
        assert out["date"].is_monotonic_increasing and not out["date"].duplicated().any()
        assert (out["tr_pct"].dropna() > 0).all() and (out["atr_prev_pct"].dropna() > 0).all()
        scored = out[out["window"].isin(["tune", "test"])]
        assert (scored["date"] > pd.Timestamp(config.KRONOS_RELEASE)).all()
        assert scored.loc[scored["window"] == "tune", "scorable"].sum() > 0
        assert scored.loc[scored["window"] == "test", "scorable"].sum() > 0

        # Parity with an independent implementation (playbook 8.2): the `ta` library's Wilder ATR, through t-1.
        atr_ta_prev = AverageTrueRange(out["high"], out["low"], out["close"], window=config.ATR_PERIOD,
                                       fillna=False).average_true_range().shift(1)
        mine_prev = out["atr_prev_pct"] * out["close"].shift(1) / 100
        in_windows = out["window"].isin(["tune", "test"])
        parity = float(((mine_prev - atr_ta_prev).abs() / atr_ta_prev)[in_windows].max())
        assert parity < 1e-9, f"{name}: ATR differs from the ta library by {parity:.2e}"

        frames[name] = out
        dropped_raw = raw[name][~raw[name]["date"].isin(kept["date"])]
        c, tu, te = f"CLEAN-{name}", f"TUNE-{name}", f"TEST-{name}"
        groups |= {
            c: f"{name} rows after cleaning, snapshot {config.SNAPSHOT_ID}",
            tu: f"{name} days in the tuning window {config.TUNE_START} to {config.TUNE_END}",
            te: f"{name} days in the test window {config.TEST_START} to {last_complete.date()}",
        }
        facts += [F.fact(f"dropped_{r}", dropped[r], c, f"rows removed: {r} (cleaning step {i + 1})")
                  for i, r in enumerate(DROP_ORDER)]
        facts += [
            F.fact("rows", len(out), c, "rows kept"),
            F.fact("first_date", str(out["date"].min().date()), c, "first kept date"),
            F.fact("last_date", str(out["date"].max().date()), c, "last kept date (last complete day)"),
            F.fact("atr_parity_max_rel_diff", parity, c,
                   "largest relative gap between our ATR(14) and the ta library's, tuning + test rows"),
            F.fact(f"missing_sessions_{name}", len(missing), "CALENDAR", f"{name}: official sessions with no bar in the data"),
            F.fact(f"extra_rows_{name}", len(extra), "CALENDAR", f"{name}: bars on dates that are not sessions"),
        ]
        for g, win in ((tu, "tune"), (te, "test")):
            w = out[out["window"] == win]
            facts += [
                F.fact("rows", len(w), g, "rows in the window"),
                F.fact("scorable_days", int(w["scorable"].sum()), g, "days that will be scored (the n of every metric)"),
                F.fact("unscorable_days", int((~w["scorable"]).sum()), g, "days in the window that are not scored"),
            ]
            bad = w[~w["scorable"]]
            if len(bad):
                tables.append({"title": f"{name} {win}: days not scored", "group": g, "columns": ["date", "weekday", "why"],
                               "rows": [[str(r.date.date()), r.date.day_name()[:3],
                                         "previous session missing from the data" if has_values[i] else "no forecast yet"]
                                        for i, r in bad.iterrows()]})
        if missing:
            tables.append({"title": f"{name}: official sessions missing from the data", "group": "CALENDAR",
                           "columns": ["date", "weekday", "effect"],
                           "rows": [[str(d.date()), d.day_name()[:3], "next session is not scored"] for d in missing]})
        tables.append({"title": f"{name}: rows removed by cleaning", "group": c, "columns": ["date", "weekday", "reason"],
                       "rows": [[str(r.date.date()), r.date.day_name()[:3], reason_for(r, pull_day, muhurat["date"])]
                                for _, r in dropped_raw.iterrows()]})

    calendar_files = sorted(config.CALENDAR_DIR.glob("*.*"))
    meta = {
        "step": "01_clean_target_atr",
        "raw_snapshot": config.SNAPSHOT_ID,
        "raw_sha256": {n: f["sha256"] for n, f in manifest["files"].items()},
        "calendar_sha256": {p.name: sha256_file(p) for p in calendar_files},
        "columns": OUT_COLS,
    }
    frames_out = {n: f.assign(date=f["date"].dt.strftime("%Y-%m-%d"))[OUT_COLS] for n, f in frames.items()}
    clean_manifest = write_derived(config.CLEAN_DIR / config.SNAPSHOT_ID, frames_out, meta)
    facts += [F.fact(f"clean_sha256_{n}", f["sha256"], "CALENDAR", f"sha256 of the cleaned {n}.csv")
              for n, f in clean_manifest["files"].items()]

    path = F.write_step(config.FACTS_DIR, "01", "Clean, calendar check, target and baselines", "01_clean_target_atr.py",
                        groups, facts, tables)
    print(f"wrote {path.relative_to(config.ROOT)}: {len(facts)} facts, {len(tables)} tables")
    for n, f in clean_manifest["files"].items():
        print(f"  clean {n}: {f['rows']} rows  sha256 {f['sha256'][:16]}…")


def reason_for(row, pull_day, muhurat_dates) -> str:
    if row.date >= pull_day:
        return "pull day (unfinished bar)"
    if pd.isna(row[["open", "high", "low", "close"]]).any():
        return "missing price"
    if row.date in set(pd.to_datetime(list(muhurat_dates))):
        return "Muhurat session"
    return "impossible bar"


if __name__ == "__main__":
    main()
