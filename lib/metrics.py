"""Scoring (Chunk 4): calibration (D8), errors, coverage, interval score, block bootstrap (D10), verdict (D11).

Everything works on plain arrays of TR% (one value per scored day), so tuning and test call the same code.
"""
import numpy as np


# --- Calibration (D8): fitted on the tuning window only, then frozen ---

def fit_kronos(actual, median_raw) -> dict:
    """One scale factor k = median(actual / Kronos median). The band is scaled by the same k."""
    r = _ratios(actual, median_raw)
    return {"scale": float(np.median(r))}


def fit_baseline(actual, point_raw, band=(0.10, 0.90)) -> dict:
    """A baseline has no band of its own: point = median ratio x forecast, band = 10th/90th ratio x forecast."""
    r = _ratios(actual, point_raw)
    lo, mid, hi = np.quantile(r, [band[0], 0.5, band[1]])
    return {"scale": float(mid), "band_lo": float(lo), "band_hi": float(hi)}


def apply_kronos(cal: dict, median_raw, p10_raw, p90_raw):
    k = cal["scale"]
    return k * np.asarray(median_raw), k * np.asarray(p10_raw), k * np.asarray(p90_raw)


def apply_baseline(cal: dict, point_raw):
    p = np.asarray(point_raw)
    return cal["scale"] * p, cal["band_lo"] * p, cal["band_hi"] * p


def _ratios(actual, forecast) -> np.ndarray:
    actual, forecast = np.asarray(actual, dtype=float), np.asarray(forecast, dtype=float)
    if actual.shape != forecast.shape or len(actual) == 0:
        raise ValueError("actual and forecast must be non-empty and the same shape")
    if np.isnan(actual).any() or np.isnan(forecast).any() or (forecast <= 0).any():
        raise ValueError("forecasts must be positive and nothing may be NaN")
    return actual / forecast


# --- Scores ---

def mae(actual, point) -> float:
    return float(np.mean(np.abs(np.asarray(actual) - np.asarray(point))))


def coverage(actual, lo, hi) -> float:
    """Share of days whose actual value lies inside the band, ends included."""
    a = np.asarray(actual)
    return float(np.mean((a >= np.asarray(lo)) & (a <= np.asarray(hi))))


def interval_score(actual, lo, hi, alpha: float) -> float:
    """Gneiting & Raftery (2007) interval score for a central (1 - alpha) band, averaged over days. Lower is
    better: band width, plus 2/alpha times how far the actual value fell outside the band."""
    a, lo, hi = (np.asarray(v, dtype=float) for v in (actual, lo, hi))
    s = (hi - lo) + (2 / alpha) * np.maximum(lo - a, 0) + (2 / alpha) * np.maximum(a - hi, 0)
    return float(np.mean(s))


def closer_share(actual, point_a, point_b) -> dict:
    """Share of days on which forecast a was strictly closer than b, and the share of exact ties."""
    ea = np.abs(np.asarray(actual) - np.asarray(point_a))
    eb = np.abs(np.asarray(actual) - np.asarray(point_b))
    return {"a_closer": float(np.mean(ea < eb)), "ties": float(np.mean(ea == eb))}


def score(actual, point, lo, hi, alpha: float) -> dict:
    return {"n": int(len(actual)), "mae": mae(actual, point), "coverage": coverage(actual, lo, hi),
            "mean_band_width": float(np.mean(np.asarray(hi) - np.asarray(lo))),
            "interval_score": interval_score(actual, lo, hi, alpha)}


# --- Moving-block bootstrap (D10) ---

def block_indices(n: int, block: int, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """(n_boot, n) resampled day indices. Each resample glues together runs of `block` consecutive days, each
    run starting at a uniform position in [0, n - block], then trims to n days (Kuensch 1989). Neighbouring days
    stay together, so volatility clustering survives the resampling."""
    if not 1 <= block <= n:
        raise ValueError(f"block length {block} must be between 1 and n = {n}")
    n_blocks = -(-n // block)
    starts = rng.integers(0, n - block + 1, size=(n_boot, n_blocks))
    return (starts[:, :, None] + np.arange(block)).reshape(n_boot, -1)[:, :n]


def mae_ratio_ci(actual, point_a, point_b, block: int, n_boot: int, seed: int, level: float = 0.95) -> dict:
    """MAE(a) / MAE(b) with a percentile CI. Both methods are resampled on the same days (paired)."""
    ea = np.abs(np.asarray(actual) - np.asarray(point_a))
    eb = np.abs(np.asarray(actual) - np.asarray(point_b))
    idx = block_indices(len(ea), block, n_boot, np.random.default_rng(seed))
    ratios = ea[idx].sum(axis=1) / eb[idx].sum(axis=1)
    tail = (1 - level) / 2
    lo, hi = np.quantile(ratios, [tail, 1 - tail])
    return {"ratio": float(ea.sum() / eb.sum()), "ci_low": float(lo), "ci_high": float(hi)}


# --- Verdict (D11) ---

def verdict(mae_ratio: float, ci_high: float, cov: float, max_ratio: float, ci_high_below: float,
            coverage_range: tuple) -> dict:
    """Gate 1 passes only if all three hold."""
    checks = {
        "mae_ratio_ok": mae_ratio <= max_ratio,
        "ci_high_ok": ci_high < ci_high_below,
        "coverage_ok": coverage_range[0] <= cov <= coverage_range[1],
    }
    return {**checks, "pass": all(checks.values())}
