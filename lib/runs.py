"""Run Kronos over many days and cache the samples. Tuning and test both call these (ground rule 5).

Samples are expensive to make and are model output on market data, so they live in out/samples/ (not in git).
A cache file is reused only if every setting stored in it equals the requested settings; a mismatch raises
instead of silently reusing or overwriting it.
"""
import json
import os
from pathlib import Path

import torch

import numpy as np
import pandas as pd

import config
from lib.forecast import sample_tr_pct, summarise
from lib.kronos_model import context_window, day_seed, sample_next_bar
from lib.snapshot import load_raw, verify_snapshot


class StaleCache(RuntimeError):
    """A samples file exists but was made with different settings or data."""


def load_clean(snapshot_id: str, name: str) -> pd.DataFrame:
    """Cleaned bars for one index from step 01 (manifest verified on read), with dates parsed."""
    df = load_raw(config.CLEAN_DIR / snapshot_id, name)
    return df.assign(date=pd.to_datetime(df["date"]))


def samples_for_days(predictor, bars: pd.DataFrame, days, index: str, n: int, T: float, top_p: float,
                     base_seed: int, context_days: int) -> np.ndarray:
    """(days, n, 4) sampled open/high/low/close; day t sees only the context_days rows before it."""
    out = np.empty((len(days), n, 4), dtype=np.float32)
    for i, t in enumerate(days):
        window = context_window(bars, t, context_days)
        out[i] = sample_next_bar(predictor, window, t, n, T, top_p, day_seed(base_seed, index, t))
    return out


def cached_samples(path, meta: dict, compute) -> tuple[np.ndarray, bool]:
    """Return (samples, computed). meta must be JSON-serialisable and fully describe how the samples were made."""
    path = Path(path)
    meta_json = json.dumps(meta, sort_keys=True)
    if path.exists():
        with np.load(path) as f:
            stored = str(f["meta"])
            if stored != meta_json:
                diff = {k for k in set(meta) | set(json.loads(stored))
                        if meta.get(k) != json.loads(stored).get(k)}
                raise StaleCache(f"{path.name} was made with different {sorted(diff)}; delete it to recompute")
            return f["samples"], False
    samples = compute()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial.npz")
    np.savez(tmp, samples=samples, meta=np.array(meta_json))
    os.replace(tmp, path)  # atomic: a crash never leaves a half-written cache file
    return samples, True


def forecast_table(bars: pd.DataFrame, days, samples: np.ndarray) -> pd.DataFrame:
    """One row per day: actual TR%, the two baselines, and Kronos's raw (uncalibrated) median and band."""
    rows = bars.set_index("date").loc[pd.DatetimeIndex(days)]
    prev_close = bars.set_index("date")["close"].shift(1).loc[pd.DatetimeIndex(days)].to_numpy()
    s = summarise(sample_tr_pct(samples, prev_close))
    return pd.DataFrame({
        "date": pd.DatetimeIndex(days),
        "tr_pct": rows["tr_pct"].to_numpy(),
        "atr_prev_pct": rows["atr_prev_pct"].to_numpy(),
        "naive_prev_pct": rows["naive_prev_pct"].to_numpy(),
        "kronos_p10": s["p10"], "kronos_median": s["median"], "kronos_p90": s["p90"],
        "kronos_distinct": s["distinct"],
    })


def window_forecasts(predictor, snapshot_id: str, index: str, window: str, T: float, top_p: float,
                     seed: int) -> tuple[pd.DataFrame, bool]:
    """Forecast table for the scorable days of one window ('tune' or 'test'), samples cached on disk.
    Returns (table, computed): computed is False when the samples came from the cache."""
    bars = load_clean(snapshot_id, index)
    days = bars.loc[(bars["window"] == window) & bars["scorable"], "date"].reset_index(drop=True)
    if days.empty:
        raise ValueError(f"{index}: no scorable days in the {window} window")
    clean_sha = verify_snapshot(config.CLEAN_DIR / snapshot_id)["files"][index]["sha256"]
    meta = {"index": index, "window": window, "days": [str(d.date()) for d in days], "n": config.N_SAMPLES,
            "T": T, "top_p": top_p, "top_k": config.TOP_K, "seed": seed, "context_days": config.CONTEXT_DAYS,
            "device": str(predictor.device), "torch": torch.__version__, "threads": torch.get_num_threads(),
            "kronos_commit": config.KRONOS_COMMIT, "model_sha256": config.KRONOS_MODEL_SHA256,
            "tokenizer_sha256": config.KRONOS_TOKENIZER_SHA256, "clean_sha256": clean_sha}
    path = config.SAMPLES_DIR / snapshot_id / window / f"{index}_T{T}_p{top_p}_seed{seed}.npz"
    samples, computed = cached_samples(path, meta, lambda: samples_for_days(
        predictor, bars, days, index, config.N_SAMPLES, T, top_p, seed, config.CONTEXT_DAYS))
    return forecast_table(bars, days, samples), computed
