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
    ("lib/features.py", 'return pd.concat([df["high"], prev_close], axis=1).max(axis=1, skipna=False) - pd.concat(\n        [df["low"], prev_close], axis=1\n    ).min(axis=1, skipna=False)',
     'return (df["high"] - df["low"]).where(prev_close.notna())', "true range = high - low (ignores gaps)"),
    ("lib/features.py", "out[seed] = v[start : seed + 1].mean()", "out[seed] = v[start]", "ATR seeded with first TR"),
    ("lib/nse_calendar.py", "return dates.isin(expected) & expected_prev.notna() & (dates.shift(1) == expected_prev)",
     "return dates.isin(expected) & expected_prev.notna()", "scorable ignores the data's previous row"),
    ("lib/clean.py", '"muhurat_session": lambda d: d["date"].isin(muhurat),', '"muhurat_session": lambda d: d["date"].isin([]),', "Muhurat rows not dropped"),
    ("lib/features.py", 'out["naive_prev_pct"] = out["tr_pct"].shift(1)', 'out["naive_prev_pct"] = out["tr_pct"]', "naive baseline uses day t"),
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
