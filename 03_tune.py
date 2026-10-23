"""Step 03: tune on the tuning window (Chunk 6, D9). Writes out/chosen.json and out/facts/03.json.

Runs only after PREREG.md is committed and pushed. For each index and each (T, top_p) in the grid: sample the
scorable tuning days, fit the calibration on those days (D8), score. The chosen setting has the lowest Kronos MAE /
ATR MAE averaged over both indices (calibrated, in-sample); ties go to the earlier grid entry. The calibration of the
chosen setting is frozen into chosen.json for the test. Touches no test-window day (D27).
"""
import json
import time

import numpy as np
import pandas as pd

import config
from lib import evaluate as E
from lib import facts as F
from lib.kronos_model import load_predictor
from lib.provenance import git_state, prereg_record, versions
from lib.runs import window_forecasts
from lib.snapshot import verify_snapshot
from lib.windows import check_windows

CHOSEN = config.ROOT / "out" / "chosen.json"


def main():
    check_windows(config.KRONOS_RELEASE, config.TUNE_START, config.TUNE_END, config.TEST_START)
    prereg = prereg_record(config.ROOT)
    raw_manifest = verify_snapshot(config.RAW_DIR / config.SNAPSHOT_ID)
    clean_manifest = verify_snapshot(config.CLEAN_DIR / config.SNAPSHOT_ID)
    predictor = load_predictor(config.KRONOS_DEVICE)
    seed = config.SEEDS[0]

    results, computed, started = {}, 0, time.perf_counter()
    for name in config.TICKERS:
        for T, top_p in config.TUNE_GRID:
            table, made = window_forecasts(predictor, config.SNAPSHOT_ID, name, "tune", T, top_p, seed)
            assert (table["date"] > pd.Timestamp(config.KRONOS_RELEASE)).all()
            assert (table["date"] <= pd.Timestamp(config.TUNE_END)).all(), "a tuning day falls in the test window"
            cal = E.fit(table)
            results[(name, T, top_p)] = {"table": table, "cal": cal, "score": E.score_all(table, cal, with_ci=False)}
            computed += made
    sampling_seconds = time.perf_counter() - started

    mean_ratio = {(T, p): float(np.mean([results[(n, T, p)]["score"]["kronos_vs_atr"]["ratio"] for n in config.TICKERS]))
                  for T, p in config.TUNE_GRID}
    T, top_p = E.choose(mean_ratio, config.TUNE_GRID)

    chosen = {
        "T": T, "top_p": top_p, "top_k": config.TOP_K, "mean_tune_ratio": mean_ratio[(T, top_p)],
        "calibration": {n: results[(n, T, top_p)]["cal"] for n in config.TICKERS},
        "tune_days": {n: len(results[(n, T, top_p)]["table"]) for n in config.TICKERS},
        "n_samples": config.N_SAMPLES, "seeds": config.SEEDS, "context_days": config.CONTEXT_DAYS,
        "device": config.KRONOS_DEVICE, "band": config.BAND,
        "snapshot_id": config.SNAPSHOT_ID,
        "raw_sha256": {n: f["sha256"] for n, f in raw_manifest["files"].items()},
        "clean_sha256": {n: f["sha256"] for n, f in clean_manifest["files"].items()},
        "kronos": {"commit": config.KRONOS_COMMIT, "model": config.KRONOS_MODEL, "model_rev": config.KRONOS_MODEL_REV,
                   "model_sha256": config.KRONOS_MODEL_SHA256, "tokenizer": config.KRONOS_TOKENIZER,
                   "tokenizer_rev": config.KRONOS_TOKENIZER_REV, "tokenizer_sha256": config.KRONOS_TOKENIZER_SHA256},
        "prereg": prereg, "code": git_state(config.ROOT, ignore=("out/", "FACTS.md")), "versions": versions(),
    }
    CHOSEN.write_text(json.dumps(chosen, indent=2, sort_keys=True) + "\n")

    out_dir = config.ROOT / "out" / "tune"  # per-day tables: derived market data, not in git (D19)
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in config.TICKERS:
        r = results[(n, T, top_p)]
        E.apply(r["table"], r["cal"]).to_csv(out_dir / f"{n}.csv", index=False, lineterminator="\n",
                                             float_format="%.6f")

    write_facts(results, mean_ratio, chosen, computed, sampling_seconds)
    print(f"chosen T={T} top_p={top_p}: mean tune ratio {mean_ratio[(T, top_p)]:.4f}; wrote {CHOSEN.relative_to(config.ROOT)}")


def write_facts(results, mean_ratio, chosen, computed, sampling_seconds):
    T, top_p = chosen["T"], chosen["top_p"]
    n_days = ", ".join(f"{n} n = {d}" for n, d in chosen["tune_days"].items())
    g, gc, gt = "TUNE-GRID", "TUNE-CHOSEN", "TUNE-RUN"
    groups = {
        g: f"tuning window {config.TUNE_START} to {config.TUNE_END}, scorable days ({n_days}), seed {config.SEEDS[0]}, "
           f"{config.N_SAMPLES} samples/day; calibration fitted and scored on the same days (in-sample)",
        gc: f"the chosen setting T={T}, top_p={top_p}, on the tuning window; these factors are frozen for the test",
        gt: "how the tuning run was made",
    }
    facts = [
        F.fact("chosen_T", T, gc, "sampling temperature chosen (D9)"),
        F.fact("chosen_top_p", top_p, gc, "nucleus threshold chosen (D9)"),
        F.fact("chosen_mean_ratio", chosen["mean_tune_ratio"], gc, "Kronos MAE / ATR MAE, mean of both indices"),
    ]
    for n in config.TICKERS:
        r = results[(n, T, top_p)]
        s, cal = r["score"], r["cal"]
        facts += [
            F.fact(f"{n}_kronos_scale", cal["kronos"]["scale"], gc, f"{n}: Kronos calibration factor (median actual / median forecast)"),
            F.fact(f"{n}_atr_scale", cal["atr"]["scale"], gc, f"{n}: ATR calibration factor (median actual / ATR)"),
            F.fact(f"{n}_atr_band", [round(cal["atr"]["band_lo"], 4), round(cal["atr"]["band_hi"], 4)], gc,
                   f"{n}: ATR band as multiples of ATR (10th, 90th percentile of actual / ATR)"),
            F.fact(f"{n}_naive_scale", cal["naive"]["scale"], gc, f"{n}: naive calibration factor"),
            F.fact(f"{n}_kronos_coverage", s["kronos"]["coverage"], gc, f"{n}: share of tuning days inside the calibrated Kronos band"),
            F.fact(f"{n}_atr_coverage", s["atr"]["coverage"], gc, f"{n}: share inside the ATR band (80% by construction, in-sample)"),
            F.fact(f"{n}_naive_vs_atr_ratio", s["naive_vs_atr"]["ratio"], gc, f"{n}: naive MAE / ATR MAE (context)"),
        ]
    facts += [
        F.fact("prereg_commit", chosen["prereg"]["commit"], gt, "commit that froze PREREG.md (pushed before this run)"),
        F.fact("prereg_committed_utc", chosen["prereg"]["committed_utc"], gt, "when PREREG.md was committed"),
        F.fact("sample_files_computed", computed, gt, "sample files made in this run (0 = all reused from cache)"),
        F.fact("sampling_seconds", sampling_seconds, gt, "wall-clock for sampling + scoring (a measurement)"),
    ]
    rows = []
    for T_, p_ in config.TUNE_GRID:
        row = [T_, p_]
        for n in config.TICKERS:
            s = results[(n, T_, p_)]["score"]
            row += [f"{s['kronos_vs_atr']['ratio']:.4f}", f"{s['kronos']['coverage']:.3f}", f"{s['distinct_median']:.0f}"]
        row += [f"{mean_ratio[(T_, p_)]:.4f}", "chosen" if [T_, p_] == [T, top_p] else ""]
        rows.append(row)
    cols = ["T", "top_p"]
    for n in config.TICKERS:
        cols += [f"{n} ratio", f"{n} coverage", f"{n} distinct values"]
    cols += ["mean ratio", ""]
    tables = [{"title": "Tuning grid: Kronos MAE / ATR MAE (calibrated), Kronos band coverage, distinct sample TR% values "
                        "per day (median)", "group": g, "columns": cols, "rows": rows}]
    detail = []
    for n in config.TICKERS:
        s = results[(n, T, top_p)]["score"]
        for m in E.METHODS:
            detail.append([n, m, f"{s[m]['mae']:.4f}", f"{s[m]['mae_raw']:.4f}", f"{s[m]['coverage']:.3f}",
                           f"{s[m]['mean_band_width']:.4f}", f"{s[m]['interval_score']:.4f}"])
    tables.append({"title": "Chosen setting on the tuning window, per method (TR% points)", "group": gc,
                   "columns": ["index", "method", "MAE", "MAE raw", "coverage", "band width", "interval score"],
                   "rows": detail})
    F.write_step(config.FACTS_DIR, "03", "Tuning (Sep-Dec 2025)", "03_tune.py", groups, facts, tables)


if __name__ == "__main__":
    main()
