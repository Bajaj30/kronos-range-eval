"""Step 02: Kronos smoke test (Chunk 2).

Checks the pins, runs upstream's own regression test, shows the averaging trap, checks the fast sampler against
upstream sample by sample on real windows, checks seeds, times both paths, and prints a first forecast for the
last few days BEFORE the tuning window (never tune or test days: D27). Writes out/facts/02.json.
Timings are measurements, so they differ slightly between runs; every other fact is deterministic.
"""
import os
import re
import subprocess
import sys
import time

import numpy as np
import pandas as pd
import torch

import config
from lib import facts as F
from lib.forecast import sample_tr_pct, summarise
from lib.kronos_model import (KRONOS_DIR, PRICE_COLS, check_code_pin, context_window, day_seed, load_predictor,
                              sample_next_bar, sample_upstream)
from lib.runs import load_clean

SMOKE_DAYS = 5  # the last rows before TUNE_START
PARITY_N = 500  # upstream holds all n copies in memory at once, so the parity check uses fewer than N_SAMPLES
DEFAULT_T, DEFAULT_TOP_P = 1.0, 0.9  # upstream predict() defaults, for the first look only


def upstream_regression() -> int:
    """Kronos's own regression test (pinned revisions, CPU, greedy decoding) in our environment."""
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_kronos_regression.py", "-q", "-p", "no:cacheprovider",
                        "-c", os.devnull, "--rootdir", "."], cwd=KRONOS_DIR, capture_output=True, text=True,
                       env={**os.environ, "PYTHONPATH": str(KRONOS_DIR)})
    if r.returncode != 0:
        raise AssertionError(f"upstream regression test failed:\n{r.stdout[-2000:]}")
    return int(re.search(r"(\d+) passed", r.stdout).group(1))


def main():
    commit = check_code_pin()
    regression_passed = upstream_regression()
    predictor = load_predictor(config.KRONOS_DEVICE)
    bars = load_clean(config.SNAPSHOT_ID, "NIFTY")
    days = bars.loc[bars["date"] < pd.Timestamp(config.TUNE_START), "date"].iloc[-SMOKE_DAYS:]
    assert (days > pd.Timestamp(config.KRONOS_RELEASE)).all() and (days < pd.Timestamp(config.TUNE_START)).all()

    # 1. The trap: sample_count > 1 returns one averaged row.
    w0, t0 = context_window(bars, days.iloc[0], config.CONTEXT_DAYS), days.iloc[0]
    torch.manual_seed(0)
    averaged = predictor.predict(w0[PRICE_COLS], w0["date"], pd.Series([t0]), pred_len=1, T=DEFAULT_T, top_k=config.TOP_K,
                                 top_p=DEFAULT_TOP_P, sample_count=5, verbose=False)

    # 2. Parity and timing on every smoke day: fast sampler vs upstream predict_batch on copies, same seed.
    parity_rows, fast_s, upstream_s = 0, [], []
    for t in days:
        w, seed = context_window(bars, t, config.CONTEXT_DAYS), day_seed(config.SEEDS[0], "NIFTY", t)
        a0 = time.perf_counter()
        fast = sample_next_bar(predictor, w, t, PARITY_N, DEFAULT_T, DEFAULT_TOP_P, seed)
        a1 = time.perf_counter()
        ref = sample_upstream(predictor, w, t, PARITY_N, DEFAULT_T, DEFAULT_TOP_P, seed)
        a2 = time.perf_counter()
        parity_rows += int((fast == ref).all(axis=1).sum())
        upstream_s.append((a2 - a1) / PARITY_N)
    assert parity_rows == PARITY_N * len(days), f"fast sampler differs from upstream on {PARITY_N * len(days) - parity_rows} samples"

    # 3. Seeds, and the first forecast at the production sample count (raw: no calibration yet).
    samples, prev_close = [], []
    for t in days:
        w, seed = context_window(bars, t, config.CONTEXT_DAYS), day_seed(config.SEEDS[0], "NIFTY", t)
        a0 = time.perf_counter()
        s = sample_next_bar(predictor, w, t, config.N_SAMPLES, DEFAULT_T, DEFAULT_TOP_P, seed)
        fast_s.append(time.perf_counter() - a0)
        samples.append(s)
        prev_close.append(w["close"].iloc[-1])
    again = sample_next_bar(predictor, w, t, config.N_SAMPLES, DEFAULT_T, DEFAULT_TOP_P, seed)
    other = sample_next_bar(predictor, w, t, config.N_SAMPLES, DEFAULT_T, DEFAULT_TOP_P, seed + 1)
    summary = summarise(sample_tr_pct(np.stack(samples), np.array(prev_close)))

    tune_days = sum(int(load_clean(config.SNAPSHOT_ID, n).eval("window == 'tune' and scorable").sum()) for n in config.TICKERS)
    test_days = sum(int(load_clean(config.SNAPSHOT_ID, n).eval("window == 'test' and scorable").sum()) for n in config.TICKERS)
    day_runs = len(config.TUNE_GRID) * tune_days + len(config.SEEDS) * test_days
    fast_per_day = float(np.median(fast_s))
    upstream_per_sample = float(np.median(upstream_s))

    g, gt = "SMOKE", "TIMING"
    groups = {
        g: f"Kronos-small smoke test on NIFTY, the {SMOKE_DAYS} days before {config.TUNE_START} "
           f"({days.iloc[0].date()} to {days.iloc[-1].date()}); T={DEFAULT_T}, top_p={DEFAULT_TOP_P}",
        gt: f"wall-clock on this machine, device={config.KRONOS_DEVICE}, torch {torch.__version__}, "
            f"{torch.get_num_threads()} threads (a measurement: varies run to run)",
    }
    facts = [
        F.fact("kronos_commit", commit, g, "vendor/Kronos HEAD, equal to the pin, no local edits"),
        F.fact("weights_sha256_verified", "yes", g, "model and tokenizer safetensors match the pinned sha256"),
        F.fact("upstream_regression_tests_passed", regression_passed, g,
               "Kronos's own regression tests (pinned revisions, greedy decoding) passing in this environment"),
        F.fact("rows_from_predict_sample_count_5", len(averaged), g, "upstream predict(sample_count=5) returns ONE averaged row"),
        F.fact("parity_samples_compared", PARITY_N * len(days), g, f"{PARITY_N} samples x {len(days)} days, same seeds"),
        F.fact("parity_samples_identical", parity_rows, g, "fast sampler == upstream predict_batch on copies, bit for bit"),
        F.fact("same_seed_identical", bool(np.array_equal(s, again)), g, "rerun with the same seed gives identical samples"),
        F.fact("new_seed_differs", bool(not np.array_equal(s, other)), g, "a different seed gives different samples"),
        F.fact("n_samples", config.N_SAMPLES, g, "samples per day (production count, D5)"),
        F.fact("median_distinct_tr_values", float(np.median(summary["distinct"])), g,
               "distinct TR% values among the samples of a day, median over the smoke days (outputs are tokens)"),
        F.fact("fast_seconds_per_day", fast_per_day, gt, f"fast sampler, {config.N_SAMPLES} samples, median over days"),
        F.fact("upstream_ms_per_sample", upstream_per_sample * 1000, gt, f"upstream predict_batch on {PARITY_N} copies"),
        F.fact("planned_day_runs", day_runs, gt,
               f"{len(config.TUNE_GRID)} configs x tune days + {len(config.SEEDS)} seeds x test days, both indices"),
        F.fact("planned_minutes_fast_estimate", day_runs * fast_per_day / 60, gt, "estimate: day runs x fast seconds per day"),
        F.fact("planned_hours_upstream_estimate", day_runs * config.N_SAMPLES * upstream_per_sample / 3600, gt,
               "estimate: the same plan through upstream copies"),
    ]
    table_rows = []
    for i, t in enumerate(days):
        row = bars.loc[bars["date"] == t].iloc[0]
        table_rows.append([str(t.date()), t.day_name()[:3], f"{row.tr_pct:.3f}", f"{row.atr_prev_pct:.3f}",
                           f"{row.naive_prev_pct:.3f}", f"{summary['median'][i]:.3f}",
                           f"{summary['p10'][i]:.3f} – {summary['p90'][i]:.3f}", int(summary["distinct"][i])])
    tables = [{"title": "First look: raw (uncalibrated) forecasts vs the actual true range, % of previous close",
               "group": g, "columns": ["date", "day", "actual TR%", "ATR(14)%", "naive%", "Kronos median%",
                                       "Kronos 10–90%", "distinct sample values"], "rows": table_rows}]
    path = F.write_step(config.FACTS_DIR, "02", "Kronos smoke test, sampler parity and timing", "02_kronos_smoke.py",
                        groups, facts, tables)
    print(f"wrote {path.relative_to(config.ROOT)}")
    for r in table_rows:
        print("  ", *r)


if __name__ == "__main__":
    main()
