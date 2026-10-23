"""Kronos-small at pinned code and weights, and one-day-ahead sampling (Chunk 2).

Upstream's predict()/predict_batch() average all sample paths into one row (spec trap 1). The spec's fix is to
feed the same window n times with sample_count=1. sample_next_bar() does the same arithmetic as that call, in the
same order of random draws, but sends the window through the tokenizer and transformer once instead of n times,
and decodes each distinct sampled token pair once. tests/test_02_kronos.py checks it sample by sample against
upstream predict_batch (D28).
"""
import hashlib
import subprocess
import sys
import warnings

import numpy as np
import pandas as pd
import torch

import config
from lib.snapshot import sha256_file

KRONOS_DIR = config.ROOT / "vendor" / "Kronos"
PRICE_COLS = ["open", "high", "low", "close"]
# Upstream calc_time_stamps uses .dt.weekday, deprecated in pandas 3 (still correct in the pinned pandas).
warnings.filterwarnings("ignore", message="Series.dt.weekday is deprecated")
if str(KRONOS_DIR) not in sys.path:
    sys.path.insert(0, str(KRONOS_DIR))
from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: E402  (pinned submodule)
from model.kronos import calc_time_stamps, sample_from_logits  # noqa: E402


class PinMismatch(RuntimeError):
    """The Kronos code or weights on disk are not the pinned ones."""


def check_code_pin() -> str:
    head = subprocess.run(["git", "-C", str(KRONOS_DIR), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
    if head != config.KRONOS_COMMIT:
        raise PinMismatch(f"vendor/Kronos is at {head[:12]}, pinned {config.KRONOS_COMMIT[:12]}")
    dirty = subprocess.run(["git", "-C", str(KRONOS_DIR), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise PinMismatch(f"vendor/Kronos has local edits:\n{dirty}")
    return head


def weights_sha256(repo_id: str, revision: str) -> str:
    from huggingface_hub import hf_hub_download

    return sha256_file(hf_hub_download(repo_id, "model.safetensors", revision=revision))


def load_predictor(device: str) -> KronosPredictor:
    """Pinned code + pinned weights (by revision and by file sha256), in eval mode."""
    check_code_pin()
    for repo, rev, sha in ((config.KRONOS_MODEL, config.KRONOS_MODEL_REV, config.KRONOS_MODEL_SHA256),
                           (config.KRONOS_TOKENIZER, config.KRONOS_TOKENIZER_REV, config.KRONOS_TOKENIZER_SHA256)):
        actual = weights_sha256(repo, rev)
        if actual != sha:
            raise PinMismatch(f"{repo}@{rev[:12]}: weights sha256 {actual[:12]}… != pinned {sha[:12]}…")
    tokenizer = KronosTokenizer.from_pretrained(config.KRONOS_TOKENIZER, revision=config.KRONOS_TOKENIZER_REV).eval()
    model = Kronos.from_pretrained(config.KRONOS_MODEL, revision=config.KRONOS_MODEL_REV).eval()
    # Eval mode matters beyond dropout: upstream's cross-attention is causal only in training mode.
    assert not tokenizer.training and not model.training
    return KronosPredictor(model, tokenizer, device=device, max_context=config.KRONOS_MAX_CONTEXT)


def context_window(bars: pd.DataFrame, t, length: int) -> pd.DataFrame:
    """The `length` rows strictly before day t (ground rule 1). Raises if there is not enough history."""
    t = pd.Timestamp(t)
    before = bars[bars["date"] < t]
    if len(before) < length:
        raise ValueError(f"{t.date()}: only {len(before)} rows before it, need {length}")
    window = before.iloc[-length:].reset_index(drop=True)
    check_context(window, t)
    return window


def check_context(window: pd.DataFrame, t) -> None:
    """The guard used at the point of sampling: no row of the input may be dated t or later."""
    last = pd.Timestamp(window["date"].iloc[-1])
    if not window["date"].is_monotonic_increasing or last >= pd.Timestamp(t):
        raise AssertionError(f"context for {pd.Timestamp(t).date()} ends {last.date()}: future rows in the input")


def day_seed(base_seed: int, index: str, t) -> int:
    """One seed per (base seed, index, day), independent of settings and run order, so every tuning config
    sees the same random draws on a given day (common random numbers) and any day can be rerun alone."""
    key = f"{base_seed}|{index}|{pd.Timestamp(t).date()}".encode()
    return int(hashlib.sha256(key).hexdigest()[:8], 16)


def _normalise(window: pd.DataFrame, clip: float):
    """Exactly upstream predict_batch's preparation: zero volume/amount, per-window z-score, clip."""
    x = window[PRICE_COLS].assign(volume=0.0, amount=0.0).to_numpy(dtype=np.float32)
    if np.isnan(x).any():
        raise ValueError("window contains NaN prices")
    mean, std = np.mean(x, axis=0), np.std(x, axis=0)
    x = np.clip((x - mean) / (std + 1e-5), -clip, clip)
    stamp = calc_time_stamps(window["date"].reset_index(drop=True)).to_numpy(dtype=np.float32)
    return x, stamp, mean, std


def sample_next_bar(predictor: KronosPredictor, window: pd.DataFrame, t, n: int, T: float, top_p: float,
                    seed: int) -> np.ndarray:
    """n sampled bars for day t, as an (n, 4) float32 array of open, high, low, close in price units.

    Same steps as upstream auto_regressive_inference with pred_len=1 on n copies: encode the window, run the
    transformer, sample s1 for n rows, sample s2 given each row's s1, decode, de-normalise. Shared work is
    done once; the random draws are the same two multinomial calls on (n, vocab) tensors as upstream.
    """
    check_context(window, t)
    if len(window) + 1 > predictor.max_context:
        raise ValueError("window + 1 bar must fit the model context (upstream would start sliding)")
    x, stamp, mean, std = _normalise(window, predictor.clip)
    dev = predictor.device
    torch.manual_seed(seed)
    with torch.no_grad():
        x_t = torch.clip(torch.from_numpy(x[None]).to(dev), -predictor.clip, predictor.clip)
        stamp_t = torch.from_numpy(stamp[None]).to(dev)
        s1_ctx, s2_ctx = predictor.tokenizer.encode(x_t, half=True)  # (1, L) each
        s1_logits, hidden = predictor.model.decode_s1(s1_ctx, s2_ctx, stamp_t)
        s1 = sample_from_logits(s1_logits[:, -1, :].expand(n, -1), temperature=T, top_k=config.TOP_K, top_p=top_p)  # (n, 1)

        s2 = sample_from_logits(s2_logits_per_row(predictor.model, hidden, s1), temperature=T, top_k=config.TOP_K,
                                top_p=top_p)  # (n, 1)

        pairs, pair_inv = torch.unique(torch.cat([s1, s2], dim=1), dim=0, return_inverse=True)
        u = len(pairs)
        pre = torch.cat([s1_ctx.expand(u, -1), pairs[:, :1]], dim=1)
        post = torch.cat([s2_ctx.expand(u, -1), pairs[:, 1:]], dim=1)
        z = predictor.tokenizer.decode([pre, post], half=True)[:, -1, :]  # (u, 6), normalised units
        z = z[pair_inv].cpu().numpy()
    bars = z * (std + 1e-5) + mean  # float32, as upstream
    return bars[:, :4]


def s2_logits_per_row(model, hidden: torch.Tensor, s1: torch.Tensor) -> torch.Tensor:
    """Last-position s2 logits for each row's sampled s1 token (n, vocab), running upstream decode_s2 once per
    distinct s1 and copying the result to the rows that drew it. hidden is the (1, L, d) transformer output."""
    s1_unique, s1_inv = torch.unique(s1[:, 0], return_inverse=True)
    logits = model.decode_s2(hidden.expand(len(s1_unique), -1, -1), s1_unique[:, None])[:, -1, :]
    return logits[s1_inv]


def sample_upstream(predictor: KronosPredictor, window: pd.DataFrame, t, n: int, T: float, top_p: float,
                    seed: int) -> np.ndarray:
    """Reference path: upstream predict_batch on n copies, sample_count=1 (the spec's method). Slow; used to check
    sample_next_bar and in the smoke step."""
    check_context(window, t)
    torch.manual_seed(seed)
    xs, ys = window["date"].reset_index(drop=True), pd.Series([pd.Timestamp(t)])
    out = predictor.predict_batch([window[PRICE_COLS]] * n, [xs] * n, [ys] * n, pred_len=1, T=T, top_k=config.TOP_K,
                                  top_p=top_p, sample_count=1, verbose=False)
    return np.stack([o[PRICE_COLS].to_numpy()[0] for o in out])
