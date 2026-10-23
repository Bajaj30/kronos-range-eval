"""From sampled bars to a range forecast (Chunk 3).

A sampled bar's four prices are separate model outputs, so a sample can have high < open or low > close.
Its high and low are therefore the max and min of all four prices (D6); its true range uses the same formula
as the target (lib.features.tr_points). Per day the forecast is the median of the samples' TR%, with the
10th-90th percentile as the band (D5). Percentiles use numpy's default linear interpolation.
"""
import numpy as np

from lib.features import tr_points

QUANTILES = (0.10, 0.50, 0.90)


def sample_tr_pct(samples: np.ndarray, prev_close) -> np.ndarray:
    """samples (..., n, 4) open/high/low/close; prev_close broadcastable to (...). Returns TR% with shape (..., n)."""
    samples = np.asarray(samples, dtype=float)
    if samples.shape[-1] != 4:
        raise ValueError(f"last axis must be open, high, low, close; got shape {samples.shape}")
    prev = np.asarray(prev_close, dtype=float)[..., None]
    high, low = samples.max(axis=-1), samples.min(axis=-1)
    return tr_points(high, low, prev) / prev * 100


def summarise(tr_samples: np.ndarray) -> dict:
    """(days, n) sample TR% -> per-day arrays: p10, median, p90, and how many distinct values the samples took."""
    tr_samples = np.asarray(tr_samples, dtype=float)
    if tr_samples.ndim != 2 or np.isnan(tr_samples).any():
        raise ValueError("expected a (days, n) array without NaN")
    p10, med, p90 = np.quantile(tr_samples, QUANTILES, axis=1)
    distinct = np.array([len(np.unique(row)) for row in tr_samples])
    return {"p10": p10, "median": med, "p90": p90, "distinct": distinct}
