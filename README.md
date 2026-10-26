# Kronos vs ATR: next-day NIFTY range forecast test (v1)

Does a pre-trained time-series foundation model ([Kronos](https://github.com/shiyu-coder/Kronos), the small model) forecast tomorrow's NIFTY 50 trading range better than the classic ATR(14) rule? The test uses only days after the model was published, so it cannot have seen them.

**Status: stopped after tuning.** The pipeline, the model wrapper, the metrics, the pre-registration and the tuning run are all done. The single pre-registered test on 2026 data was **not run** on purpose (see below). Every number on this page is copied from the generated [FACTS.md](FACTS.md).

---

## Summary

### The question
**What is forecast:** tomorrow's *true range*, the distance between the day's high and low, extended to the previous close if the market gaps. It is expressed as a % of the previous close.

**Who wins:** a forecast wins if its mean absolute error (MAE) is lower. The contenders:
- **Kronos-small:** 5,000 sampled next-day bars per day. The point forecast is their median; the band is their 10th–90th percentile.
- **ATR(14):** the standard trader's rule.
- A "tomorrow = today" baseline, for context.

Each method gets one scale factor fitted on the tuning days, in the same way for all three.

**Gate 1 (from the project design, fixed in [PREREG.md](PREREG.md) before any tuning):**
1. Kronos MAE ÷ ATR MAE ≤ 0.95;
2. the 95% block-bootstrap CI of that ratio stays below 1.00;
3. Kronos's 10–90% band contains 75–85% of actual days.

### Tuning result
Tuning window: 2025-09-01 to 2025-12-31, 83 scored days per index (FACTS step 03). The ratio is Kronos MAE ÷ ATR MAE, so **below 1 means Kronos is better**. Coverage is the share of days inside Kronos's 10–90% band (target about 0.80). Calibration was fitted and scored on these same days, so these numbers are in-sample and flattering to both methods.

| T | top_p | NIFTY ratio | NIFTY coverage | NIFTY distinct values | BANKNIFTY ratio | BANKNIFTY coverage | BANKNIFTY distinct values | mean ratio |  |
|---|---|---|---|---|---|---|---|---|---|
| 0.6 | 0.9 | 1.1658 | 0.651 | 12 | 1.2380 | 0.747 | 12 | 1.2019 | chosen |
| 0.6 | 0.99 | 1.1733 | 0.711 | 24 | 1.2446 | 0.807 | 35 | 1.2089 |  |
| 0.8 | 0.9 | 1.1385 | 0.759 | 15 | 1.3093 | 0.831 | 18 | 1.2239 |  |
| 0.8 | 0.99 | 1.1676 | 0.831 | 42 | 1.3317 | 0.819 | 50 | 1.2497 |  |
| 1 | 0.9 | 1.1575 | 0.819 | 18 | 1.3422 | 0.831 | 28 | 1.2498 |  |
| 1 | 0.99 | 1.1519 | 0.904 | 70 | 1.4318 | 0.880 | 120 | 1.2918 |  |

- *T* (temperature) and *top_p* control how widely Kronos samples.
- "Distinct values" is the median number of different range values among a day's 5,000 samples. Kronos outputs tokens, so its samples are lumpy.
- At the chosen setting on NIFTY, Kronos's MAE is 0.1872 percentage points of range against ATR's 0.1606 (FACTS step 03, per-method table).

### Verdict
- **There is no Gate 1 verdict, because the test was not run.**
- **On the tuning days, Kronos-small lost to ATR(14) at all 6 settings, on both indices.** Its error was 14–43% higher (ratios 1.1385–1.4318), against a pass bar of ≤ 0.95.
- **At the chosen setting, the NIFTY band was too narrow:** it held 0.651 of days against a 0.75–0.85 target.
- **Taken together:** with daily bars and this setup, Kronos-small does not beat a 14-day average of past ranges. Following the project design's Gate 1, it would be demoted to one input among many rather than the core range forecast.

### Why the test was not run
1. **Tuning already answered the practical question.** No setting came close to the pass bar on either index. Even the best was well above 1.
2. **The pre-registered selection rule turned out to be flawed.**
   - It picks the setting with the lowest error only, but Gate 1 also judges the band.
   - The lowest-error setting is also the one with the narrowest band (fewest distinct sample values), so it was set up to fail coverage.
   - Running the one-shot test would spend the 2026 data on a design already known to be wrong. The rule was not quietly changed after the fact; the flaw is reported here instead.
3. **The 2026 test window stays unopened.**
   - No 2026 forecast or error has been computed: `04_test.py` never ran, and its run log `out/test_runs.log` does not exist.
   - A corrected v2 can be pre-registered and still be tested on days nobody has looked at. That data is worth more unused than spent on a known-flawed design.

[PREREG.md](PREREG.md) promised to publish the test result whatever it was. No test result exists, and this page says so.

### Limits
- **Not out-of-sample:** the evidence is in-sample tuning on 83 days per index, roughly four months. The two indices move together, so BANKNIFTY is not independent evidence.
- **Narrow setup:** daily bars only, prices only (open, high, low, close; Yahoo's index volume is unreliable, FACTS step 00), Kronos-small only, a 400-day context, and one sampling method. Kronos-base, intraday bars or fine-tuning could behave differently.
- **Lumpy samples:** a day's samples take only a handful of distinct values (FACTS step 02, `median_distinct_tr_values`), so the bands are coarse.
- **Blind to the calendar:** for a one-day forecast, Kronos never sees the target day's date, so it cannot know a weekend or holiday comes first. ATR cannot either.
- **Pretraining overlap:** Kronos's pretraining data includes Indian markets up to mid-2024. Tuning and test days come after the model's public release (2 Aug 2025); the 400-day context windows reach back before it, as inputs only.
- **Free data:** Yahoo Finance data, with its quirks. One session is missing (the 1 Feb 2026 Budget Sunday), and the pull's 23 Oct 2026 bar had no close (FACTS step 01).

---

## What was built (the pipeline)
Each step is a script. Each writes its numbers to `out/facts/<step>.json`, and `facts.py` renders them into [FACTS.md](FACTS.md).

| step | what it does | evidence (FACTS) |
|---|---|---|
| `00_pull_data.py` | Pulls daily bars for `^NSEI` and `^NSEBANK` from 2015 into an immutable snapshot with a sha256 manifest. A re-run only verifies; it never re-downloads. | step 00: 2,916 / 2,917 raw rows |
| `00b_profile.py` | Counts every kind of bad bar, gap and volume problem before trusting the data. Volume is unreliable, so only prices are used. | step 00 |
| `01_clean_target_atr.py` | Cleans the bars in a fixed order (unfinished bar → missing price → one-hour Muhurat sessions → impossible bars), then reconciles every row against NSE's official trading calendar. It computes the target, ATR(14) and the naive baseline, and diffs the frozen pull against an earlier pull to detect vendor revisions. | step 01: 302 expected sessions, 0 extra rows; ATR matches the `ta` library to 7.162e-16; 83 tuning and 197 test days per index |
| `02_kronos_smoke.py` | Checks Kronos is the pinned code and weights, runs Kronos's own regression tests, shows that its built-in sampling silently averages, checks our sampler against upstream sample by sample, and times both. | step 02: 4 upstream tests pass; 2,500 / 2,500 samples identical; 0.2561 s per day vs 41.81 ms per sample upstream |
| `03_tune.py` | Runs the 6-setting grid on both indices, fits the calibration, picks a setting by the pre-registered rule, and freezes it in `out/chosen.json`. | step 03 (table above); step 03b: regenerating the chosen samples gives the identical 1,660,000 values per index |
| `04_test.py` | The one test run, with refusals built in: no second run unless forced and counted, no changed data, PREREG or code. **Written and committed with PREREG; never run.** | — |

**Engineering points worth a look:**
- **Faster sampling, proven identical.**
  - Kronos's `sample_count` returns the *average* of its samples, not the samples. The standard workaround feeds the same 400-day window thousands of times, repeating identical work.
  - `lib/kronos_model.py` does the shared work once per day and draws all samples from it.
  - It is bit-identical to upstream (tests plus FACTS step 02), and it cut the estimated plan from 126.5 hours to 9.297 minutes on a laptop CPU (FACTS step 02, estimates).
- **Pinned and verified:** Kronos is a git submodule at a fixed commit; its weights are pinned by revision *and* by file sha256. Data snapshots are hashed and verified on every read.
- **Pre-registration enforced in code:**
  - Tuning refuses to start unless [PREREG.md](PREREG.md) is committed and pushed.
  - The test refuses if anything changed since tuning.
  - The test counts each attempt in an append-only log before touching test data.
- **Tests that are themselves tested:** `tools/mutation_check.py` plants realistic bugs, such as an unshifted ATR, a forecast that sees day *t*, or an unpaired bootstrap, and requires a failing test for each. It catches every one.
- **Generated numbers:** [FACTS.md](FACTS.md) is rendered from the steps' outputs and is never hand-edited.

## Reproduce
```bash
git clone --recurse-submodules https://github.com/Bajaj30/kronos-range-eval && cd kronos-range-eval
uv sync
uv run pytest -q && uv run python -m tools.mutation_check   # needs no market data; downloads the pinned Kronos weights once
```
To rerun the pipeline on your own pull:
1. In `config.py`, set `SNAPSHOT_ID` to a new id and `COMPARE_SNAPSHOT_ID = None`. The committed snapshots only hold manifests; their CSVs are not redistributed.
2. Run:
   ```bash
   uv run python 00_pull_data.py && uv run python 00b_profile.py && uv run python 01_clean_target_atr.py
   uv run python 02_kronos_smoke.py && uv run python 03_tune.py   # a few minutes on CPU
   uv run python facts.py
   ```

Yahoo serves today's data, so a new pull will not match the frozen snapshot's hashes. `data/raw/frozen-2026-10-24/manifest.json` and `out/chosen.json` record exactly what was used. Market data, raw or derived, and Kronos's samples are not redistributed.

## Repo map
- `config.py`: every setting.
- [PREREG.md](PREREG.md): the frozen plan and its known limits.
- [FACTS.md](FACTS.md): every number.
- `lib/`:
  - data: snapshots, cleaning, the NSE calendar, features;
  - model: `kronos_model.py` (sampler), `forecast.py` (samples → forecast);
  - scoring and guards: `metrics.py` (calibration, MAE, coverage, interval score, block bootstrap, verdict), `evaluate.py`, `provenance.py`.
- `tests/`: one file per stage.
- `tools/`: the mutation check, the determinism re-check, and the NSE holiday-list fetcher.
- `vendor/Kronos`: upstream, pinned and untouched.
- `data/calendar/`: official holiday lists and sourced special-session tables.
- `out/`: facts and `chosen.json`.
