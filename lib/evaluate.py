"""From a forecast table (lib.runs.forecast_table) to calibrated forecasts and scores.

Tuning fits the calibration and scores on the same days; the test applies the frozen calibration and scores.
Both go through these functions (ground rules 4 and 5: every method is calibrated the same way, in one place).
"""
import numpy as np
import pandas as pd

import config
from lib import metrics as M

METHODS = ("kronos", "atr", "naive")
RAW_POINT = {"kronos": "kronos_median", "atr": "atr_prev_pct", "naive": "naive_prev_pct"}
ALPHA = round(1 - (config.BAND[1] - config.BAND[0]), 10)  # 0.2: the band is a central 80% interval


def fit(table: pd.DataFrame) -> dict:
    y = table["tr_pct"]
    return {"kronos": M.fit_kronos(y, table["kronos_median"]),
            "atr": M.fit_baseline(y, table["atr_prev_pct"], config.BAND),
            "naive": M.fit_baseline(y, table["naive_prev_pct"], config.BAND)}


def apply(table: pd.DataFrame, cal: dict) -> pd.DataFrame:
    """Per day: actual, and each method's calibrated point and band."""
    out = table[["date", "tr_pct"]].copy()
    out["kronos_point"], out["kronos_lo"], out["kronos_hi"] = M.apply_kronos(
        cal["kronos"], table["kronos_median"], table["kronos_p10"], table["kronos_p90"])
    for m in ("atr", "naive"):
        out[f"{m}_point"], out[f"{m}_lo"], out[f"{m}_hi"] = M.apply_baseline(cal[m], table[RAW_POINT[m]])
    return out


def score_all(table: pd.DataFrame, cal: dict, with_ci: bool) -> dict:
    """Scores for every method, the headline ratio Kronos MAE / ATR MAE (with its block-bootstrap CI if asked),
    the naive / ATR ratio for context, and raw (uncalibrated) errors."""
    c = apply(table, cal)
    y = c["tr_pct"].to_numpy()
    out = {m: M.score(y, c[f"{m}_point"], c[f"{m}_lo"], c[f"{m}_hi"], ALPHA) for m in METHODS}
    for m in METHODS:
        out[m]["mae_raw"] = M.mae(y, table[RAW_POINT[m]])
    out["kronos_vs_atr"] = {"ratio": out["kronos"]["mae"] / out["atr"]["mae"],
                            "ratio_raw": out["kronos"]["mae_raw"] / out["atr"]["mae_raw"],
                            **M.closer_share(y, c["kronos_point"], c["atr_point"])}
    out["naive_vs_atr"] = {"ratio": out["naive"]["mae"] / out["atr"]["mae"]}
    if with_ci:
        ci = M.mae_ratio_ci(y, c["kronos_point"], c["atr_point"], config.BOOT_BLOCK, config.BOOT_N, config.BOOT_SEED,
                            config.CI_LEVEL)
        assert np.isclose(ci["ratio"], out["kronos_vs_atr"]["ratio"], rtol=1e-12)
        out["kronos_vs_atr"] |= {"ci_low": ci["ci_low"], "ci_high": ci["ci_high"]}
    out["distinct_median"] = float(np.median(table["kronos_distinct"]))
    return out


def choose(mean_ratio: dict, grid: list) -> list:
    """D9: the grid setting with the lowest mean Kronos / ATR ratio; on a tie, the earlier setting in the grid."""
    return min(grid, key=lambda setting: mean_ratio[tuple(setting)])  # min returns the first of equal values
