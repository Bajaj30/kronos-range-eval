"""Step 04: the one test run (Chunk 7). Writes out/results.json and out/facts/04.json.

Refuses to run if: PREREG.md changed since the commit recorded at tuning; the snapshot or cleaned data changed
since tuning; tracked code has uncommitted edits; or the test already ran (unless --force, which is counted in
test_runs and reported). Uses the frozen setting and calibration from out/chosen.json, with no refit.
The headline is NIFTY with the first seed; the other seeds are the seed check (D12).
"""
import argparse
import json
from datetime import datetime, timezone

import config
from lib import evaluate as E
from lib import facts as F
from lib import metrics as M
from lib.kronos_model import load_predictor
from lib.provenance import git_state, prereg_record, start_run, versions
from lib.runs import window_forecasts
from lib.snapshot import sha256_file, verify_snapshot

CHOSEN = config.ROOT / "out" / "chosen.json"
RESULTS = config.ROOT / "out" / "results.json"
RUN_LOG = config.ROOT / "out" / "test_runs.log"  # append-only, in git
HEADLINE_INDEX = "NIFTY"


def preflight(force: bool) -> tuple[dict, int, dict]:
    """Every refusal happens before any test-window forecast is made; the run is counted last."""
    chosen = json.loads(CHOSEN.read_text())
    prereg = prereg_record(config.ROOT)
    if prereg["sha256"] != chosen["prereg"]["sha256"]:
        raise RuntimeError("PREREG.md changed after tuning")
    if chosen["snapshot_id"] != config.SNAPSHOT_ID:
        raise RuntimeError(f"config points at snapshot {config.SNAPSHOT_ID}, tuning used {chosen['snapshot_id']}")
    raw = verify_snapshot(config.RAW_DIR / config.SNAPSHOT_ID)  # raises if any raw file changed
    clean = verify_snapshot(config.CLEAN_DIR / config.SNAPSHOT_ID)
    for kind, manifest in (("raw", raw), ("clean", clean)):
        now = {n: f["sha256"] for n, f in manifest["files"].items()}
        if now != chosen[f"{kind}_sha256"]:
            raise RuntimeError(f"{kind} data differs from the data used for tuning")
    code = git_state(config.ROOT, ignore=("out/", "FACTS.md"))
    if code["dirty"]:
        raise RuntimeError(f"uncommitted edits in {code['edited']}; commit first so the result names its code")
    note = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} commit {code['commit'][:12]} force={force}"
    run_number = start_run(RUN_LOG, force, note)
    return chosen, run_number, code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="run again; counted in test_runs and reported")
    args = ap.parse_args()
    chosen, run_number, code = preflight(args.force)
    predictor = load_predictor(chosen["device"])

    per = {}
    for name in config.TICKERS:
        cal = chosen["calibration"][name]
        for seed in chosen["seeds"]:
            table, _ = window_forecasts(predictor, config.SNAPSHOT_ID, name, "test", chosen["T"], chosen["top_p"], seed)
            per[(name, seed)] = {"table": table, "score": E.score_all(table, cal, with_ci=True)}

    head = per[(HEADLINE_INDEX, chosen["seeds"][0])]["score"]
    k = head["kronos_vs_atr"]
    verdict = M.verdict(k["ratio"], k["ci_high"], head["kronos"]["coverage"], config.PASS_MAX_RATIO,
                        config.PASS_CI_HIGH_BELOW, config.PASS_COVERAGE)
    results = {
        "test_runs": run_number,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "headline": {"index": HEADLINE_INDEX, "seed": chosen["seeds"][0], **k,
                     "kronos_coverage": head["kronos"]["coverage"], "verdict": verdict},
        "scores": {f"{n}/seed{s}": v["score"] for (n, s), v in per.items()},
        "test_days": {n: len(per[(n, chosen["seeds"][0])]["table"]) for n in config.TICKERS},
        "first_last_day": {n: [str(per[(n, chosen["seeds"][0])]["table"]["date"].min().date()),
                               str(per[(n, chosen["seeds"][0])]["table"]["date"].max().date())] for n in config.TICKERS},
        "provenance": {"chosen_sha256": sha256_file(CHOSEN), "prereg": chosen["prereg"], "code": code,
                       "snapshot_id": config.SNAPSHOT_ID, "raw_sha256": chosen["raw_sha256"],
                       "clean_sha256": chosen["clean_sha256"], "kronos": chosen["kronos"], "versions": versions(),
                       "device": chosen["device"]},
    }
    RESULTS.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")

    out_dir = config.ROOT / "out" / "test"  # per-day tables: derived market data, not in git until Chunk 8 decides
    out_dir.mkdir(parents=True, exist_ok=True)
    for (n, s), v in per.items():
        E.apply(v["table"], chosen["calibration"][n]).to_csv(out_dir / f"{n}_seed{s}.csv", index=False,
                                                             lineterminator="\n", float_format="%.6f")
    write_facts(results, chosen)
    print(f"test run {run_number}: {HEADLINE_INDEX} Kronos/ATR MAE ratio {k['ratio']:.4f} "
          f"[{k['ci_low']:.4f}, {k['ci_high']:.4f}], coverage {head['kronos']['coverage']:.3f}, pass={verdict['pass']}")


def write_facts(results, chosen):
    groups, facts, rows = {}, [], []
    for n in config.TICKERS:
        first, last = results["first_last_day"][n]
        g = f"TEST-{n}"
        groups[g] = (f"{n} test window {first} to {last}, n = {results['test_days'][n]} scored days, T={chosen['T']}, "
                     f"top_p={chosen['top_p']}, {chosen['n_samples']} samples/day, frozen calibration")
        for s in chosen["seeds"]:
            sc = results["scores"][f"{n}/seed{s}"]
            kv = sc["kronos_vs_atr"]
            rows.append([n, s, f"{kv['ratio']:.4f}", f"{kv['ci_low']:.4f} – {kv['ci_high']:.4f}",
                         f"{sc['kronos']['coverage']:.3f}", f"{kv['a_closer']:.3f}"])
        sc = results["scores"][f"{n}/seed{chosen['seeds'][0]}"]
        kv = sc["kronos_vs_atr"]
        facts += [
            F.fact("mae_ratio", kv["ratio"], g, "Kronos MAE / ATR MAE, calibrated (headline seed)"),
            F.fact("mae_ratio_ci", [round(kv["ci_low"], 4), round(kv["ci_high"], 4)], g,
                   f"{config.CI_LEVEL:.0%} moving-block bootstrap CI ({config.BOOT_N} resamples, {config.BOOT_BLOCK}-day blocks)"),
            F.fact("mae_ratio_raw", kv["ratio_raw"], g, "the same ratio without calibration"),
            F.fact("kronos_closer_share", kv["a_closer"], g, "share of days Kronos's point forecast was strictly closer than ATR's"),
            F.fact("naive_vs_atr_ratio", sc["naive_vs_atr"]["ratio"], g, "naive MAE / ATR MAE (context)"),
        ]
        for m in E.METHODS:
            facts += [
                F.fact(f"{m}_mae", sc[m]["mae"], g, f"{m}: mean absolute error, TR% points (calibrated)"),
                F.fact(f"{m}_coverage", sc[m]["coverage"], g, f"{m}: share of days inside the calibrated 10-90 band"),
                F.fact(f"{m}_band_width", sc[m]["mean_band_width"], g, f"{m}: mean band width, TR% points"),
                F.fact(f"{m}_interval_score", sc[m]["interval_score"], g, f"{m}: interval score (lower is better)"),
            ]
    h = results["headline"]
    groups["VERDICT"] = f"Gate 1 (D11) on the headline: {h['index']} test window, seed {h['seed']}"
    facts += [
        F.fact("pass", h["verdict"]["pass"], "VERDICT", "all three conditions hold"),
        F.fact("mae_ratio_ok", h["verdict"]["mae_ratio_ok"], "VERDICT", f"ratio <= {config.PASS_MAX_RATIO}"),
        F.fact("ci_high_ok", h["verdict"]["ci_high_ok"], "VERDICT", f"CI upper end < {config.PASS_CI_HIGH_BELOW}"),
        F.fact("coverage_ok", h["verdict"]["coverage_ok"], "VERDICT", f"Kronos coverage within {config.PASS_COVERAGE}"),
        F.fact("test_runs", results["test_runs"], "VERDICT", "times the test has run (1 = never rerun)"),
        F.fact("code_commit", results["provenance"]["code"]["commit"], "VERDICT", "repo commit the test ran on"),
    ]
    tables = [{"title": "Seed check (D12): the same test with each seed", "group": "VERDICT",
               "columns": ["index", "seed", "MAE ratio", "95% CI", "Kronos coverage", "Kronos closer share"],
               "rows": rows}]
    F.write_step(config.FACTS_DIR, "04", "Test (2026, run once)", "04_test.py", groups, facts, tables)


if __name__ == "__main__":
    main()
