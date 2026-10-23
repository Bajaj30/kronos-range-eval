# Pre-registration: Kronos vs ATR, next-day range (v1)

This file fixes every setting and rule **before** any tuning output exists. It is committed and pushed to GitHub first.
- `03_tune.py` refuses to run unless this file is committed, unchanged and pushed.
- `04_test.py` also refuses if this file changed after tuning.
- The code that tunes and tests (`03_tune.py`, `04_test.py`, `lib/`) is committed together with this file.

## 1. Question
Does Kronos-small forecast tomorrow's true range of the NIFTY 50 index better than ATR(14)? Only trading days after Kronos's public release (arXiv 2508.02739, 2 Aug 2025) count, so the model cannot have seen them. Nifty Bank (BANKNIFTY) gets the same treatment and is reported as secondary evidence.

## 2. Data
- **Source:** Yahoo Finance daily bars through `yfinance` (`^NSEI`, `^NSEBANK`) from 2015-01-01, as received (`auto_adjust=False`).
- **Frozen snapshot:**
  - It is pulled **once, after this commit**, as snapshot `frozen-2026-10-24`. Every file's sha256 goes into its manifest and is copied into `out/chosen.json` and `out/results.json`.
  - The test refuses to run if any file changed after tuning.
  - The last scored day is the last complete trading day before the pull day (IST).
- **Cleaning, in this order:**
  1. the unfinished pull-day bar;
  2. rows with a missing price;
  3. Muhurat (one-hour Diwali) sessions;
  4. impossible bars (flat, high below the body, low above it, or non-positive).

  Any other defect type (duplicates, out-of-order rows, non-midnight stamps, moves over 20% from the previous close) stops the pipeline instead of being dropped.
- **Calendar check:** from 2025-08-01, every row is reconciled against NSE's official F&O holiday list, plus sourced special-session and Muhurat tables.
  - A row on a non-session day stops the pipeline.
  - A day whose previous official session is missing from the data is used as model input but **not scored**. Today this affects 2026-02-02, the day after the missing Budget-Sunday session.
- **Prices only:** open, high, low, close. Yahoo's index volume is unreliable, so Kronos gets volume = 0, which is upstream's own default when volume is absent.

## 3. Target
True range of day *t* as a percentage of the previous close:

  TR%ₜ = [max(Hₜ, Cₜ₋₁) − min(Lₜ, Cₜ₋₁)] / Cₜ₋₁ × 100

Cₜ₋₁ is the close of the previous row in the cleaned data.

## 4. Windows
- **Tuning:** scorable days from 2025-09-01 to 2025-12-31.
- **Test:** scorable days from 2026-01-01 to the last complete day of the frozen snapshot.
- **No look-ahead:** every forecast for day *t* uses only rows dated before *t* (asserted at the point of sampling).

## 5. Methods
1. **Kronos-small**
   - **Pins:**
     - code: commit `67b630e67f6a18c9e9be918d9b4337c960db1e9a`;
     - weights: `NeoQuasar/Kronos-small@901c26c1332695a2a8f243eb2f37243a37bea320`;
     - tokenizer: `NeoQuasar/Kronos-Tokenizer-base@0e0117387f39004a9016484a186a908917e22426`;
     - both safetensors files are also pinned by sha256 (`config.py`).
   - **Input:** the 400 rows before *t*. The model and tokenizer are in eval mode. The device is CPU.
   - **Samples:** 5,000 per day.
     - Temperature T and top_p come from the tuning grid; top_k is off.
     - Each day's seed is derived from (seed, index, date), so every tuning setting sees the same random draws on a given day.
     - The sampler does upstream's arithmetic once per day rather than once per copy. It is bit-identical to upstream `predict_batch` on copies with `sample_count=1` (`tests/test_02_kronos.py`; FACTS step 02).
   - **Per sample:** high = max and low = min of its four prices, so a sample with high below open still makes sense. TR% is measured against Cₜ₋₁.
   - **Per day:**
     - point forecast = median of the samples' TR%;
     - band = their 10th–90th percentile (numpy linear interpolation).
2. **ATR(14):** Wilder's ATR in points through day *t−1*, divided by Cₜ₋₁ (the chart indicator).
3. **Naive** ("tomorrow = today"): TR% of day *t−1*. Context only; not part of the verdict.

## 6. Calibration
Calibration is fitted on the tuning days only, per index and per method in the same way, then frozen.
- **Kronos:** k = median(actual ÷ Kronos median). The point and both band ends are multiplied by k.
- **ATR and naive:** they have no band of their own.
  - point = median(actual ÷ forecast) × forecast;
  - band = the 10th and 90th percentiles of actual ÷ forecast, each × forecast.
- Raw (uncalibrated) errors are reported too.

## 7. Tuning (`03_tune.py`)
- **Grid:** T ∈ {0.6, 0.8, 1.0} × top_p ∈ {0.9, 0.99}, 6 settings in this order: (0.6, 0.9), (0.6, 0.99), (0.8, 0.9), (0.8, 0.99), (1.0, 0.9), (1.0, 0.99). Seed 1, both indices.
- **Score:** for each setting and index, fit the calibration on the tuning days and compute calibrated MAE(Kronos) ÷ MAE(ATR) on the same days.
- **Choice:** the setting with the lowest mean of that ratio over the two indices. Ties go to the earlier setting in the order above.
- **Output:** `out/chosen.json` holds the setting, the calibration factors, the data hashes and this file's commit.

## 8. Test (`04_test.py`, run once)
- Uses `out/chosen.json`, with no refitting, and seeds 1, 2 and 3.
- **Headline:** NIFTY with seed 1. The headline number is the ratio MAE(Kronos) ÷ MAE(ATR), both calibrated, on the test days. Its 95% CI comes from a moving-block bootstrap:
  - 5,000 resamples of 10-day blocks;
  - paired: both methods are resampled on the same days;
  - percentile interval, bootstrap seed 7.
- **Gate 1 passes only if all three hold:**
  1. ratio ≤ 0.95;
  2. CI upper end < 1.00;
  3. the share of test days inside Kronos's calibrated 10–90 band is within [0.75, 0.85], ends included.
- **Also reported, not part of the verdict:**
  - BANKNIFTY with the same metrics;
  - the ratios for seeds 2 and 3 (seed check);
  - the raw ratio;
  - band widths and coverage of all three methods;
  - interval score (α = 0.2);
  - the share of days Kronos's point forecast was closer than ATR's;
  - naive ÷ ATR.
- **Run counting:**
  - Each run is logged in `out/test_runs.log` before it touches a test day.
  - A second run is refused unless forced, and any forced run is counted and reported (`test_runs`).
- **Reporting:** the result is published whatever it is, including a fail. If Kronos fails Gate 1, it becomes one input among many for Phase 2, as the design doc says.

## 9. Changes from the original spec (decided before this commit, with reasons in CLAUDE.md §6)
- **Compute (D29):** local CPU instead of a Kaggle GPU. The shared-work sampler makes the whole plan take minutes, and CPU results are deterministic.
- **Sampler (D28):** the shared-work sampler instead of n copies through upstream. It is proven bit-identical, and it is the reason 5,000 samples per day are affordable (D30; the spec said 30, and D5 revised that to at least 100).
- **Step numbering:** 02 smoke, 03 tune, 04 test. Metrics live in `lib/metrics.py`.

## 10. Known limits (stated before the result)
- **One stretch of market history:** about 13 months, daily bars only, roughly 200 test days per index. The two indices move together, so BANKNIFTY is not independent evidence.
- **Pretraining overlap:**
  - Kronos's pretraining data (to mid-2024, per its paper) includes NSE.
  - No tuning or test day predates the release.
  - Context windows do reach back before it, as inputs only.
- **Coarse samples:** Kronos's outputs are tokens, so one day's 5,000 samples take only a handful of distinct values (FACTS step 02, `median_distinct_tr_values`). Its percentiles are therefore coarse.
- **The target day's date is ignored:** for a one-step forecast, upstream Kronos does not use the target day's timestamp, so it cannot know a weekend or holiday comes first. ATR cannot either.
- **Calibration:** fitted on four months. The ATR band is empirical, so it covers about 80% of tuning days by construction.
- **Tuning is in-sample:** calibration and setting choice are scored on the same tuning days.
- **Reproducibility across machines:** CPU floating point can differ in the last bits on another machine or thread count, which could rarely change a sampled token. Versions and thread count are recorded.
- **One model size:** Kronos-small only. Kronos-base and Kronos-mini are later work.
