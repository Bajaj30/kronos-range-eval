# Kronos vs ATR: range forecast test (v1) — Handoff Context
> Read order: §0 → rest of this file → FACTS.md → INTERVIEW.md (local only) → spec (`../context/v1_build_baseline_testing.md`).
> Update this file at the end of every chunk.

Last updated: 2026-10-26 · Stopped after Chunk 6 (D38). The test (Chunk 7) was deliberately NOT run; README explains why.

## 0. Where we are — read this first (2026-10-26)
**State:** Chunks 0–6 are done. **v1 stopped here (D38): the single test run (Chunk 7) was not run, so the 2026 test window is still unopened.** No 2026 forecast or error exists, and `out/test_runs.log` does not exist. The README is the public write-up: question, tuning table, verdict (none; tuning says Kronos loses), why we stopped, limits.
- **Data:** the frozen snapshot `frozen-2026-10-24` was pulled after PREREG was committed. It is cleaned, reconciled against the official NSE calendar, and diffed against the explore snapshot (FACTS step 01, `REVISIONS`).
  - Yahoo's Fri 23 Oct bar had no close at pull time, so it was dropped by the pre-registered rule and the test window ends 2026-10-22 (D37).
  - The cleaned files are byte-identical to the explore build.
- **Kronos:**
  - pinned by commit and by weight sha256;
  - upstream's own regression tests pass here;
  - our shared-work sampler is bit-identical to upstream `predict_batch` on copies;
  - see FACTS step 02.
- **PREREG.md** is committed and pushed together with the tuning and test code (§8 Chunk 5).
- **Tuning is done:** `out/chosen.json` and FACTS step 03.
  - **Kronos lost to ATR at all 6 settings on both indices** (in-sample).
  - The chosen setting's NIFTY band under-covers.
  - So Gate 1 will very likely fail on the test. Per PREREG, the result is published either way.
  - Regenerating the chosen samples from scratch is bit-identical (FACTS step 03b).
- **Tests:** see §8 for counts. `tools/mutation_check.py` catches every planted bug.

**Live:** repo github.com/Bajaj30/kronos-range-eval (public), README written 2026-10-26. No site. **Headline number:** none (no test). The honest summary is the tuning table in FACTS step 03 (in-sample).

**Not in git** (D19, D36):
- raw and cleaned CSVs (`data/raw/<snap>/`, `data/clean/<snap>/`);
- Kronos samples (`out/samples/`);
- per-day forecast tables (`out/tune/*.csv`, `out/test/*.csv`);
- INTERVIEW.md;
- `.venv/`.

Rebuild with the commands below. The committed manifests and `out/chosen.json` hold the sha256 values a rebuild must match.

**Deadline:** public link before the job application. Submit Sun 25 Oct night; hard stop Mon 26 Oct 09:00 IST.

**Resume — the commands** (run from this folder; `git submodule update --init` after cloning):

| to | run |
|---|---|
| set up env | `uv sync` |
| pull or verify raw snapshot | `uv run python 00_pull_data.py` |
| profile raw data | `uv run python 00b_profile.py` |
| clean + calendar + target/baselines | `uv run python 01_clean_target_atr.py` |
| Kronos smoke test (pins, parity, timing) | `uv run python 02_kronos_smoke.py` |
| tune (needs PREREG pushed; reuses cached samples) | `uv run python 03_tune.py` |
| determinism re-check of tuning samples | `uv run python -m tools.recheck_determinism` |
| **test once (refuses a 2nd run)** | `uv run python 04_test.py` |
| regenerate FACTS.md | `uv run python facts.py` |
| tests | `uv run pytest -q` |
| test the tests | `uv run python -m tools.mutation_check` |
| refresh NSE holiday lists | `uv run python -m tools.fetch_nse_holidays --refresh` (see trap 6) |

**Open, in order of value (only if the user restarts the work):**
1. **v2 design:** a selection rule that matches the gate (MAE *and* coverage), or a band calibrated separately from the point forecast. Write a new PREREG, then use the still-unopened 2026 window.
   - Do NOT run v1's `04_test.py` first: that would open the window for v1's flawed design.
2. Chunk 8 extras (site, number-check script, resume line from FACTS), if wanted.
3. India VIX baseline (D15); Kronos-base and Kronos-mini as separate runs.

**Schedule** (spec §8 with corrected weekdays):

| day | chunks |
|---|---|
| Fri 23 Oct | 0–1 (done) |
| Sat 24 Oct | 2–6 (done), 7 on the user's OK |
| Sun 25 Oct | 8, resume, apply |
| Mon 26 Oct | buffer until 09:00 |

Cut order if behind: stretch goals → BANKNIFTY → seed check.

## 1. What this project is
Forecast tomorrow's NIFTY 50 range well enough that a trader can choose an options setup, or no trade, before the open. v1 tests whether Kronos-small beats ATR(14) at this on days after Kronos's public release. Either result is published.

v1 is a narrow slice of Phase 1 / Gate 1 of the Kronos Regime Router design (`../context/`). The resume targets an ML / data engineering role, so the pipeline's rigour is part of the story: snapshots, hashes, an official-calendar reconciliation, generated facts, and tests that are themselves tested.

## 2. How to work
- **Loop per chunk:**
  1. Claude explains the concept, the plan and the checks that could fail.
  2. We discuss.
  3. The user says "implement" or "go".
  4. Claude writes the code and updates CLAUDE.md, FACTS.md and INTERVIEW.md.
  5. The user reviews.
  6. Next chunk.
- **Exam period (from 2026-10-24, user):** the user is building "partially blind" because of exams. They trust Claude to make and document the smaller decisions, to take longer and account for everything, and they will study the project afterwards. So Claude:
  - decides the smaller questions itself, with reasons, in §6;
  - verifies its own work harder: mutation checks, independent parity checks, re-runs for determinism;
  - keeps the chat report short.
- **Division of labour:** Claude writes all the code. The user makes the big decisions and reviews when possible.
- **Numbers:** every number quoted in chat or in any doc comes from FACTS.md, which is generated. Never from memory. An estimate is labelled as an estimate.
- **INTERVIEW.md:** every problem we hit, written the day it happens: what happened, the options, what we chose and why.
- **Learning loop (playbook 12):** concept first, with an everyday comparison. The user's two-line explain-backs are deferred until after exams.
- **Machine:** Apple M4 (4 performance + 6 efficiency cores), 16 GB, Python 3.11 arm64, uv; the GitHub CLI is logged in as Bajaj30. GitHub, Hugging Face and Kaggle are all reachable from this Mac.
- **Compute:** everything runs on this Mac's CPU (D29). The shared-work sampler made the GPU unnecessary. Kaggle (free T4/P100, about 30 h/week, capped at 25 h by D16) is unused for v1, and there is no Kaggle token on this Mac.

## 3. Ground rules (from spec §3; never broken without writing why)
1. No future in any input. The forecast for day *t* uses only bars dated before *t*, for Kronos and ATR alike.
2. No pretraining overlap. Every tuning and test day comes after Kronos's public release (2 Aug 2025).
3. Freeze before testing. Settings go in PREREG.md and are committed before the test window is touched. The test runs once, and re-runs are counted and reported.
4. Same treatment for both methods. Anything fitted for Kronos is fitted for ATR the same way, on the same days.
5. Each piece of logic lives in one place. Tuning, test and the live page use the same functions.
6. Every quoted number comes from the generated FACTS.md.
7. Seeds fixed, data snapshot hashed. A rerun gives the same numbers.

## 4. Repo map
```
V1_baseline_testing/              (git repo → github.com/Bajaj30/kronos-range-eval)
  CLAUDE.md                       this file (handoff)
  PREREG.md                       every setting and the pass rule, committed + pushed before tuning (Chunk 5)
  FACTS.md                        GENERATED by facts.py, never hand-edited
  INTERVIEW.md                    problems → options → choice → why (gitignored, private)
  README.md                       public stub; full write-up in Chunk 8
  config.py                       every setting; rendered into FACTS.md (paths excluded)
  00_pull_data.py                 Yahoo → immutable snapshot + sha256 manifest; re-run = verify only
  00b_profile.py                  defects, gaps, volume quality → out/facts/00.json; prints real rows
  01_clean_target_atr.py          clean → official-calendar reconcile → TR%, ATR, naive → data/clean; snapshot diff
  02_kronos_smoke.py              pins, upstream regression tests, averaging trap, sampler parity, seeds, timing
  03_tune.py                      6-setting grid on tuning days → out/chosen.json (setting + frozen calibration)
  04_test.py                      the one test run → out/results.json; refuses reruns and changed data/code
  facts.py                        out/facts/*.json + config → FACTS.md (checks the render is deterministic)
  lib/snapshot.py                 sha256; ensure/verify snapshot; load_raw (verified read); write_derived (atomic)
  lib/bars.py                     normalise raw rows; defect masks; gaps
  lib/clean.py                    the fixed cleaning order; stops on never-seen defect types
  lib/nse_calendar.py             official holidays + special/Muhurat tables → expected sessions, reconcile, scorable
  lib/features.py                 tr_points (THE true-range formula), Wilder ATR, tr_pct / atr_prev_pct / naive_prev_pct
  lib/windows.py                  tune/test labels + release/overlap guards
  lib/kronos_model.py             pinned loader (commit + weight sha256, eval mode), context_window + guard,
                                  day_seed, sample_next_bar (shared-work sampler), sample_upstream (reference)
  lib/forecast.py                 samples → TR% (max/min of 4 prices) → median and 10–90 band
  lib/runs.py                     load_clean; samples over days; sample cache (refuses stale); forecast_table;
                                  window_forecasts (used by tune AND test)
  lib/metrics.py                  calibration fit/apply, MAE, coverage, interval score, block bootstrap, verdict
  lib/evaluate.py                 forecast table → calibrated forecasts → scores; the D9 choice rule
  lib/provenance.py               git state, PREREG commit check, versions, append-only test-run counter
  lib/facts.py                    fact records, group validation, Markdown render
  tools/fetch_nse_holidays.py     official NSE F&O holiday lists → data/calendar/nse_holidays_<year>.json
  tools/mutation_check.py         breaks the code on purpose; every mutation must fail a test
  tests/                          test_00_* (bars, snapshot, facts), test_01_* (features, clean, calendar),
                                  test_02_kronos, test_03_forecast, test_04_metrics, test_05_tune_test_guards
  vendor/Kronos/                  git submodule pinned at 67b630e (upstream code, untouched)
  data/calendar/                  nse_holidays_2025/2026.json, special_sessions.csv, muhurat_sessions.csv (in git)
  data/raw/<snapshot>/            raw CSVs (not in git) + manifest.json (in git)
  data/clean/<snapshot>/          cleaned CSVs (not in git) + manifest.json with lineage hashes (in git)
  out/facts/                      per-step facts JSON (in git)
  out/chosen.json                 tuning result: setting, frozen calibration, data + PREREG hashes (in git)
  out/samples/, out/tune/, out/test/   cached samples and per-day tables (not in git)
  pyproject.toml, uv.lock         pinned environment (torch, einops, huggingface_hub, safetensors, tqdm; dev: pytest, ta)
```

## 5. Chunk status
| chunk | scope | status |
|---|---|---|
| 0 | setup, pull and look at the data | done 2026-10-23 (FACTS step 00) |
| 1 | clean, calendar check, TR% target, ATR, naive | done 2026-10-24 (FACTS step 01) |
| 2 | Kronos smoke test, sampling trick, timing | done 2026-10-24 (FACTS step 02) |
| 3 | samples → forecast | done 2026-10-24 (`lib/forecast.py`, `lib/runs.py`) |
| 4 | metrics | done 2026-10-24 (`lib/metrics.py`, `lib/evaluate.py`) |
| 5 | pre-register | done 2026-10-24 (PREREG.md pushed; commit in FACTS step 03 `prereg_commit`) |
| 6 | tune (Sep–Dec 2025) | done 2026-10-24 (FACTS step 03, `out/chosen.json`) |
| 7 | test once (2026) | **not run (D38)**; code committed with PREREG, never executed |
| 8 | publish | README write-up done 2026-10-26; no site |

## 6. Decisions
- **D1–D14 (2026-10-23, user):** accepted as written in spec §5, except D5 below.
- **D5 revised (2026-10-23, user):** at least 100 samples per day, not 30. The final count is set after Chunk 2 measures time, then frozen in PREREG. Because the 10th/90th percentiles of 30 samples are just the 3rd and 27th values, which is too noisy for the coverage verdict. Rejected: 30.
- **D13 confirmed (2026-10-23, data):** prices only (OHLC), no volume. Because Yahoo's index volume is unreliable for both indices (FACTS step 00). Rejected: volume as an input.
- **D15 (2026-10-23, user):** India VIX becomes a second baseline after Chunks 0–8 ship. Rejected: adding it now (deadline).
- **D16 (2026-10-23, user):** spend Kaggle GPU on rigour (more samples and seeds, Kronos-base/mini as separate runs), not on more tuning configs. Capped at 25 h of the ~30 h. Rejected: a bigger tuning grid.
- **D17 (2026-10-23, user):** everything for v1 lives in `V1_baseline_testing/`. The working docs are CLAUDE.md, FACTS.md and INTERVIEW.md. INTERVIEW.md stays private.
- **D18 (2026-10-23, user):** data reaches Kaggle as an uploaded Kaggle Dataset, and the notebook verifies sha256 before use. Rejected: pulling on Kaggle.
- **D19 (2026-10-23, Claude):** market data, raw and cleaned, is not committed to the public repo; only manifests with sha256 are. Because Yahoo and NSE redistribution terms are restrictive or unclear. Rejected: committing the CSVs.
- **D20 (2026-10-23, Claude):** `yf.config.debug.hide_exceptions = False`. Because yfinance's default turns a failed download into an empty table.
- **D21 (2026-10-24, user):** drop Muhurat rows in every year. Because a one-hour session adds noise to the target, ATR and the Kronos context. Dates come from `muhurat_sessions.csv`. Every run checks each date with a NIFTY row against the published Muhurat close to the paisa (FACTS step 01: `muhurat_closes_matched`). Rejected: keeping them.
- **D22 (2026-10-24, user):** reconcile the data against NSE's official F&O holiday list from 2025-08-01 to the last complete day. An unexplained extra row stops the pipeline. Rejected: trusting Yahoo's row list.
- **D23 (2026-10-24, user, option a):** a day whose previous official session is missing from the data is kept as model input but not scored. The rule is generic (`scorable_mask`), with no hard-coded date; today it excludes only 2026-02-02. Rejected: patching the missing Budget-Sunday bar from a second source (another source to verify under deadline).
- **D24 (2026-10-24, user):** ATR = Wilder ATR(14) in points through day t−1, divided by C(t−1), which is the chart indicator. It matches the `ta` library to float precision (FACTS: `atr_parity_max_rel_diff`). Rejected: averaging TR% directly.
- **D25 (2026-10-24, Claude):**
  - **Fixed cleaning order:** pull-day → missing price → Muhurat → impossible bar → recheck = 0, all before any look-back computation.
  - **Unhandled defect types stop the pipeline:** duplicates, out-of-order rows, non-midnight stamps and spikes are never dropped silently.
  - Rejected: dropping every defect automatically (it would hide new data problems).
- **D26 (2026-10-24, Claude):** the official NSE holiday lists are stored in the repo with source URL and retrieval time. Muhurat dates live in their own sourced table. Because NSE's list omits weekday Laxmi Pujan days (2017, 2018, 2021, 2022, 2024) and once listed a "Special Live Trading" Saturday as a holiday (2024). Rejected: deriving Muhurat dates from the holiday list.
- **D27 (2026-10-24, Claude):** before PREREG, nothing looks at outcomes in the test window: no target statistics, no forecast errors. Chunk 1 reports only counts and dates there. Because looking would let test results leak into choices (spec trap 9).
- **D28 (2026-10-24, Claude):** sample with our shared-work sampler (`sample_next_bar`), not n copies through upstream `predict_batch`.
  - **How:** it runs the encoder and transformer once per day, draws the n samples with the same two multinomial calls on (n, vocab) tensors as upstream, and decodes each distinct token pair once.
  - **Evidence:** bit-identical to upstream in unit tests (3 settings) and on real NIFTY windows (FACTS step 02 `parity_samples_identical`).
  - **Because:** the spec's copies repeat identical work n times (FACTS step 02 `planned_hours_upstream_estimate` vs `planned_minutes_fast_estimate`).
  - **Rejected:** upstream copies (days of compute); patching the pinned library.
- **D29 (2026-10-24, Claude):** run on this Mac's CPU. This supersedes D18 for v1: no Kaggle.
  - **Because:** with D28 the CPU takes minutes. The M4 GPU (MPS) was measured at only about 1.7× faster per upstream sample. The CPU is deterministic and portable, and it needs nothing from the user during exams.
  - **Rejected:** Kaggle (needs a token and an upload, and it's slower end to end); MPS (less portable, little gain).
- **D30 (2026-10-24, Claude):** N = 5,000 samples per day (D5 said at least 100).
  - **Because:** the cost barely grows with n once the shared work is done. Kronos's samples are lumpy (FACTS step 02 `median_distinct_tr_values`), so precise probabilities matter for the 10th and 90th percentiles.
  - **Rejected:** 100 and 1,000.
- **D31 (2026-10-24, Claude):** each day's seed = hash(seed, index, date).
  - Every tuning setting sees the same random draws on a day (common random numbers, so setting comparisons have less noise).
  - Any day can be rerun alone, and results don't depend on run order.
  - Seeds are 1, 2 and 3: 1 is the headline and tuning seed; 2 and 3 are the seed check.
- **D32 (2026-10-24, Claude):** tuning detail.
  - Calibration is per index.
  - The choice uses calibrated ratios scored on the same tuning days (in-sample; listed as a limit).
  - Ties go to the earlier grid entry, in the order written in PREREG §7. The rule lives in `lib/evaluate.choose`.
  - **Rejected:** choosing on raw ratios (calibration is part of the deployed method).
- **D33 (2026-10-24, Claude):** pre-registration is enforced in code.
  - PREREG.md is committed together with `03_tune.py`, `04_test.py` and `lib/`.
  - Tuning refuses unless PREREG is committed, unchanged and on a remote branch.
  - The test refuses if PREREG, raw data or clean data changed since tuning, or if tracked code has uncommitted edits.
  - The test logs its run number to `out/test_runs.log` *before* touching a test day, so crashed runs count too.
  - **Rejected:** a manual promise.
- **D34 (2026-10-24, Claude):** the Chunk 2 "last 5 days" forecast print uses the last 5 days **before the tuning window**. Because the literal last 5 days are test days (D27).
- **D35 (2026-10-24, Claude):** step files are 02 smoke, 03 tune and 04 test. Metrics live in `lib/` because they are a library, not a step. **Rejected:** the spec's 02–06 numbering.
- **D38 (2026-10-26, user):** stop v1 after tuning and do not run the test.
  - The user did not give the Chunk 7 OK and asked for a README covering the question, the tuning table, the verdict, why we stopped and the limits.
  - **Reasons written in the README:**
    - tuning already showed Kronos losing at every setting;
    - the pre-registered selection rule is flawed (trap 17), so the one-shot test would be spent on a known-bad design;
    - keeping the 2026 window unopened lets a corrected v2 be tested on unseen days.
  - PREREG promised to publish the test result; no test result exists, and the README says so.
- **D37 (2026-10-24, Claude):** keep the single frozen pull even though it adds no day.
  - **What happened:** Yahoo's 2026-10-23 bar had no close at 04:40 IST the next morning; the explore pull's intraday value was a round 22600.00. The pre-registered missing-price rule dropped it, so the test window ends 2026-10-22.
  - **Because:** a second "frozen" pull to gain one day would break PREREG §2 (pulled once). One day changes nothing material.
  - **Rejected:** re-pulling later; patching the bar from another source.
- **D36 (2026-10-24, Claude):** samples and per-day forecast tables stay out of git. They contain the actual TR% series, which is derived market data (extends D19). Whether a per-day chart goes on the public site is decided in Chunk 8.

## 7. Traps (hit while building; full stories in INTERVIEW.md)
- **Known in advance:** spec §9 (14 items).
- **Hit while building:**
  1. **Silent empty download.** yfinance hides errors by default → `hide_exceptions=False` (D20).
  2. **NaN ≠ NaN.** A mismatch check counted the missing-price rows → every comparison check must be NaN-aware. When a count equals another count, ask why.
  3. **Special sessions in the bars.** Muhurat rows are tiny one-hour bars, and the Budget-Sunday session 2026-02-01 is missing from Yahoo → sourced tables plus a calendar reconcile (D21–D23).
  4. **Pipes in Markdown.** A `|` in a description split a FACTS table → `_cell` escapes pipes, and a test covers it.
  5. **A holiday list is not a session calendar.** NSE omits weekday Muhurat days, and its 2024 list has a "Special Live Trading" entry → `load_holidays` refuses session-like entries; Muhurat has its own table (D26).
  6. **NSE domain blocked mid-session.** `www.nseindia.com` resolved via `nslookup` but not via the system resolver in this sandbox, after working minutes earlier → `fetch_nse_holidays --from-dir` builds from saved API responses, keeping their retrieval time.
  7. **Rounding hid the evidence.** FACTS rendered Muhurat closes as 8626 when the point was a match to the paisa → format numbers at the producer when precision is the claim.
  8. **Tests that never failed.** All Chunk 1 tests passed first time → `tools/mutation_check.py` breaks the code 6 ways; each one must fail a test (6/6).
  9. **Derived data is still market data.** The cleaned CSVs were about to be committable → `.gitignore` covers `data/clean/**/*.csv` (D19).
  10. **Eval mode is not only about dropout.** Upstream's cross-attention is causal only in training mode → the loader asserts `.eval()`.
  11. **Device-sticky cache.** Upstream's rotary embedding caches cos/sin on the first device used. Moving the model to another device in the same process crashed → one device per process.
  12. **Weak parity test.** Kronos's fine token (s2) barely depends on the coarse one (s1), so whole-sampler parity on a few samples missed a wrong s1→s2 mapping → the mapping is tested directly. Separately, an "equivalent mutant" (a 1e-5 change below float32 precision) was replaced.
  13. **`.strip()` ate git's status column.** `" M out/x"` became `"M out/x"`, and the path parsed as `"ut/x"`. The ignore rule never matched → `rstrip("\n")`; a test covers it.
  14. **Upstream uses deprecated pandas API.** `.dt.weekday` warns in pandas 3 → pandas stays pinned in uv.lock; the warning is filtered by exact message only.
  15. **Lumpy samples.** Thousands of samples take only a handful of distinct values (tokens) → N = 5,000 (D30), reported as a limit.
  16. **"Complete" is not complete on Yahoo.** The day after, Yahoo's Friday bar still had no close, and the intraday pull's close was a placeholder-looking round number → the missing-price rule and the calendar reconcile caught it (D37). The revision diff first said "max change 0" for a value that went missing → it now prints what changed.
  17. **The selection rule ignored part of the gate.** D9 chooses on MAE only, but Gate 1 also needs coverage. The lowest-MAE setting has the narrowest bands (FACTS step 03 grid), so coverage is likely to fail too. It is pre-registered, so it stays → lesson for v2: choose on the same criteria the gate uses.

## 8. Chunk notes (plan, results, explain-back)
### Chunk 0 — setup and look at the data (done 2026-10-23)
**Results:** FACTS step 00. No duplicates, impossible bars, spikes or long gaps. Volume is unreliable (D13). The pull-day row is unfinished. Special sessions were found (→ Chunk 1).
**Explain-back:** deferred (exams).

### Chunk 1 — clean, calendar check, target, baselines (done 2026-10-24)
**Results** (numbers: FACTS step 01):
- **Calendar:** the cleaned data matches the official NSE session calendar exactly for both indices. The only exception is the missing 2026-02-01 Budget-Sunday session, and there are 0 extra rows. Muhurat dates are confirmed by published closes.
- **Scorable days:** all tuning days can be scored. In the test window, every day except 2026-02-02 can be scored.
- **ATR parity** with the `ta` library is at float precision.
- **Determinism:** the cleaned files are byte-identical across runs (`clean_sha256_*`).

**Checks that could fail (all pass; 42 tests total):**
- TR% on 3 real 2015 rows equals exact decimal hand values (normal, gap-down and gap-up cases);
- the tester fails on a value right to 4 digits but wrong at 1e-12;
- a 3-period Wilder example worked by hand;
- the perturbation test (day t untouched; t+1 moves);
- ATR(t) = ATR through t−1 ÷ C(t−1);
- the cleaning order fixes the previous close, and the wrong order gives NaN;
- never-seen defects stop the pipeline;
- the calendar's missing and extra rows are found exactly;
- the scorable rules, including after holidays, after Muhurat days and after extra rows;
- the session-like holiday entry is refused;
- the window guards hold;
- parity with `ta` on synthetic data;
- mutation check 6/6.

**Explain-back:** deferred (exams).

### Chunk 2 — Kronos smoke test, sampler, timing (done 2026-10-24)
**Results** (FACTS step 02):
- **Pins:** the commit and both weight sha256 values verified; upstream's regression tests pass in our environment.
- **Averaging trap:** `predict(sample_count=5)` returns 1 row; a test shows it equals the mean of the 5 paths that copies give.
- **Sampler:** the shared-work sampler matches upstream bit for bit on real windows (D28).
- **Seeds:** the same seed gives identical samples; a different seed gives different ones.
- **Timing:** the fast path takes well under a second per day at 5,000 samples, so the whole plan takes minutes on CPU.
- **Samples are lumpy** (trap 15).
- **First look:** a table of the 5 days before tuning (raw, uncalibrated).

**Checks that could fail:** `tests/test_02_kronos.py`:
- eval mode;
- the averaging trap reproduced numerically;
- copies differ;
- fast == upstream at 3 settings, including unfiltered;
- the s1→s2 mapping against upstream per-row;
- seeds;
- the context window is strictly before t;
- the guard fires on a window that includes t;
- too little history is refused;
- the seed derivation;
- a wrong commit pin is refused;
- a wrong weights hash is refused.

**Explain-back:** deferred (exams).

### Chunk 3 — samples → forecast (done 2026-10-24)
**What:**
- `lib/forecast.py`: each sample's high/low = max/min of its 4 prices; TR% uses the same `tr_points` formula as the target; per day the median and the 10th/90th percentiles.
- `lib/runs.py`: samples over days, a cache that refuses stale settings, and a forecast table aligned to the previous row's close.

**Checks that could fail** (`tests/test_03_forecast.py`):
- an inverted sampled bar (H < L) gives 5% by hand;
- a gap above the previous close gives 6%, not 2%;
- shapes are days × n;
- linear-interpolation quantiles match hand values;
- the forecast table uses the previous row's close (an off-by-one fails);
- the cache reuses only identical settings and leaves no partial files.

### Chunk 4 — metrics (done 2026-10-24)
**What:**
- `lib/metrics.py`: calibration (D8), MAE, inclusive coverage, interval score, closer share, paired moving-block bootstrap, verdict (D11).
- `lib/evaluate.py`: one path from a forecast table to calibrated scores, for tuning and test alike.

**Checks that could fail** (`tests/test_04_metrics.py`, `tests/test_05_tune_test_guards.py`):
- a perfect forecast gives MAE 0 and coverage 1;
- a forecast 2× too small gives a factor of exactly 2;
- the median, not the mean;
- interval score by hand;
- worse by design gives a ratio > 1 and a fail;
- verdict boundaries (inclusive/strict);
- blocks keep neighbouring days together and cover every start;
- paired and reproducible;
- the block CI is wider than the plain one on clustered errors (why D10);
- all three methods are calibrated by the same functions;
- the choice rule and its tie-break.

### Chunk 5 — pre-register (done 2026-10-24)
PREREG.md lists every setting in plain words, the pass rule, the changes from the spec (D28–D30, D35) and the known limits. It was committed and pushed together with the tuning and test code (D33), before the frozen pull and before any tuning output. Its commit and time are in FACTS step 03 (`prereg_commit`, `prereg_committed_utc`) and in `out/chosen.json`.

### Chunk 6 — tune (done 2026-10-24)
**What:**
- A fresh frozen pull, then step 01 on it, including a diff against the explore snapshot (FACTS step 01 `REVISIONS`).
- Then the 6-setting grid on both indices' scorable tuning days, the D9 choice, and the frozen calibration in `out/chosen.json`.

**Results:** FACTS step 03 (the tuning table and the chosen setting's per-method scores; in-sample).
- Kronos's MAE ratio vs ATR is above 1 at every setting on both indices; the chosen setting is T=0.6, top_p=0.9.
- Lower temperature or top_p gives fewer distinct sample values and narrower bands. On NIFTY that gives lower coverage.
- Determinism: FACTS step 03b.

**Done-when checks:** `check_windows` guards against overlap and against pre-release days. Each tuning day is asserted to come after the release and on or before TUNE_END. `chosen.json` exists, and the tuning table is in FACTS.

### Chunk 7 — test once (NOT RUN, D38; the plan below is kept for a future run)
`04_test.py` is written, tested (guards) and committed with PREREG. On the OK:
1. `uv run python 04_test.py`.
2. `uv run python facts.py`.
3. Commit `out/results.json`, `out/test_runs.log`, `out/facts/04.json` and FACTS.md.
4. Show that a second run is refused (spec done-when).
5. Show on a copy that an edited snapshot is refused.
