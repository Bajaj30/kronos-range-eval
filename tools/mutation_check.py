"""Test the tests: break the code on purpose; every mutation must make at least one test fail.

Run from the repo root: uv run python -m tools.mutation_check
Each file is restored after its mutation, even if pytest crashes. Add mutations as chunks add logic.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUTATIONS = [
    ("lib/features.py", 'out["atr_prev_pct"] = wilder_atr(tr, atr_period).shift(1) / prev_close * 100',
     'out["atr_prev_pct"] = wilder_atr(tr, atr_period) / prev_close * 100', "ATR not shifted (uses day t)"),
    ("lib/features.py", "return np.maximum(high, prev_close) - np.minimum(low, prev_close)",
     "return (high - low) + 0 * prev_close", "true range = high - low (ignores gaps)"),
    ("lib/features.py", "out[seed] = v[start : seed + 1].mean()", "out[seed] = v[start]", "ATR seeded with first TR"),
    ("lib/nse_calendar.py", "return dates.isin(expected) & expected_prev.notna() & (dates.shift(1) == expected_prev)",
     "return dates.isin(expected) & expected_prev.notna()", "scorable ignores the data's previous row"),
    ("lib/clean.py", '"muhurat_session": lambda d: d["date"].isin(muhurat),', '"muhurat_session": lambda d: d["date"].isin([]),', "Muhurat rows not dropped"),
    ("lib/features.py", 'out["naive_prev_pct"] = out["tr_pct"].shift(1)', 'out["naive_prev_pct"] = out["tr_pct"]', "naive baseline uses day t"),
    # Chunk 2: Kronos sampling
    ("lib/kronos_model.py", "    torch.manual_seed(seed)\n    with torch.no_grad():\n        x_t", "    with torch.no_grad():\n        x_t",
     "sampler ignores the seed"),
    ("lib/kronos_model.py", "return logits[s1_inv]", "return logits[torch.zeros_like(s1_inv)]", "s2 drawn for the wrong s1"),
    ("lib/kronos_model.py", "if not window[\"date\"].is_monotonic_increasing or last >= pd.Timestamp(t):",
     "if not window[\"date\"].is_monotonic_increasing or last > pd.Timestamp(t):", "guard lets day t into the input"),
    ("lib/kronos_model.py", "mean, std = np.mean(x, axis=0), np.std(x, axis=0)", "mean, std = np.mean(x, axis=0), np.std(x, axis=0, ddof=1)",
     "normalisation differs from upstream (ddof)"),
    # Chunk 3: samples -> forecast
    ("lib/forecast.py", "high, low = samples.max(axis=-1), samples.min(axis=-1)", "high, low = samples[..., 1], samples[..., 2]",
     "sampled H/L columns trusted as-is"),
    ("lib/runs.py", 'prev_close = bars.set_index("date")["close"].shift(1)', 'prev_close = bars.set_index("date")["close"]',
     "samples measured against day t's close"),
    # Chunk 4: metrics
    ("lib/metrics.py", 'return {"scale": float(np.median(r))}', 'return {"scale": float(np.mean(r))}', "calibration uses the mean ratio"),
    ("lib/metrics.py", "(starts[:, :, None] + np.arange(block))", "(starts[:, :, None] + 0 * np.arange(block))",
     "bootstrap blocks are not consecutive days"),
    ("lib/metrics.py", "return float(np.mean((a >= np.asarray(lo)) & (a <= np.asarray(hi))))",
     "return float(np.mean((a > np.asarray(lo)) & (a < np.asarray(hi))))", "coverage excludes the band ends"),
    ("lib/metrics.py", "(hi - lo) + (2 / alpha)", "(hi - lo) + (1 / alpha)", "interval score penalty halved"),
    ("lib/metrics.py", '"mae_ratio_ok": mae_ratio <= max_ratio', '"mae_ratio_ok": mae_ratio < max_ratio', "ratio limit made strict"),
    ("lib/metrics.py", "idx = block_indices(len(ea), block, n_boot, np.random.default_rng(seed))\n    ratios = ea[idx].sum(axis=1) / eb[idx].sum(axis=1)",
     "idx = block_indices(len(ea), block, n_boot, np.random.default_rng(seed))\n    ratios = ea[idx].sum(axis=1) / eb[idx[::-1]].sum(axis=1)",
     "bootstrap not paired"),
    # Chunks 6-7: choice and guards
    ("lib/evaluate.py", "return min(grid, key=lambda setting: mean_ratio[tuple(setting)])",
     "return max(grid, key=lambda setting: mean_ratio[tuple(setting)])", "tuning picks the worst setting"),
    ("lib/evaluate.py", 'return {"kronos": M.fit_kronos(y, table["kronos_median"]),', 'return {"kronos": M.fit_kronos(y, table["kronos_p90"]),',
     "Kronos calibrated on the wrong column"),
    ("lib/provenance.py", "    if previous and not force:", "    if False:", "second test run not refused"),
    ("lib/provenance.py", '    if not _git(repo, "branch", "-r", "--contains", commit):', "    if False:", "PREREG not required on GitHub"),
]
caught = 0
for file, old, new, label in MUTATIONS:
    path = ROOT / file
    original = path.read_text()
    assert old in original, f"mutation anchor not found: {label}"
    path.write_text(original.replace(old, new))
    try:
        r = subprocess.run(["uv", "run", "pytest", "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True)
    finally:
        path.write_text(original)
    ok = r.returncode != 0
    caught += ok
    first_fail = next((l for l in r.stdout.splitlines() if l.startswith("FAILED")), "no failing test")
    print(f"{'CAUGHT ' if ok else 'MISSED!'} {label:45s} -> {first_fail[:90]}")
print(f"{caught}/{len(MUTATIONS)} mutations caught")
if caught < len(MUTATIONS):
    sys.exit(1)
