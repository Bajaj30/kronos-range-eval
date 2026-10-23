"""Ground rule 7 check: regenerate the chosen setting's tuning samples from scratch and compare them, bit for bit,
with the cached file that tuning used. Writes out/facts/03b.json.

Run from the repo root after 03_tune.py: uv run python -m tools.recheck_determinism
"""
import json

import numpy as np

import config
from lib import facts as F
from lib.kronos_model import load_predictor
from lib.runs import load_clean, samples_for_days


def main():
    chosen = json.loads((config.ROOT / "out" / "chosen.json").read_text())
    T, top_p, seed = chosen["T"], chosen["top_p"], chosen["seeds"][0]
    predictor = load_predictor(chosen["device"])
    facts, groups = [], {}
    for name in config.TICKERS:
        bars = load_clean(config.SNAPSHOT_ID, name)
        days = bars.loc[(bars["window"] == "tune") & bars["scorable"], "date"].reset_index(drop=True)
        cached_path = config.SAMPLES_DIR / config.SNAPSHOT_ID / "tune" / f"{name}_T{T}_p{top_p}_seed{seed}.npz"
        with np.load(cached_path) as f:
            cached = f["samples"]
        fresh = samples_for_days(predictor, bars, days, name, config.N_SAMPLES, T, top_p, seed, config.CONTEXT_DAYS)
        g = f"RERUN-{name}"
        groups[g] = f"{name} tuning samples for the chosen setting, regenerated in a new process vs the cached file"
        facts += [F.fact("values_compared", int(fresh.size), g, "sampled prices compared (days x samples x 4)"),
                  F.fact("identical", bool(np.array_equal(fresh, cached)), g, "regenerated samples equal the cache, bit for bit")]
    F.write_step(config.FACTS_DIR, "03b", "Determinism re-check of the tuning samples", "tools/recheck_determinism.py",
                 groups, facts)
    print(*(f"{f['group']}: {f['key']} = {f['value']}" for f in facts), sep="\n")


if __name__ == "__main__":
    main()
