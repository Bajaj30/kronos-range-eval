# Kronos vs ATR: range forecast test (v1) — Handoff Context
> Read order: §0 → rest of this file → FACTS.md → INTERVIEW.md (local only) → spec (`../context/v1_build_baseline_testing.md`).
> Update this file at the end of every chunk.

Last updated: 2026-10-24 · Chunks 0–1 implemented and pushed; Chunk 2 proposed.

## 0. Where we are — read this first (2026-10-24)
**State:** Chunks 0 and 1 are done.
- The data is cleaned and checked against the official NSE calendar.
- The target (TR%) and both baselines (ATR(14), naive) are computed.
- 42 tests pass, and `tools/mutation_check.py` catches 6 of 6 deliberate bugs.
- The scored sample sizes are in FACTS.md: `TUNE-NIFTY scorable_days` and `TEST-NIFTY scorable_days`.

**Live:** repo github.com/Bajaj30/kronos-range-eval (public). No site yet. **Headline number:** none yet; it comes after Chunk 7.

**Not in git:**
- raw and cleaned CSVs in `data/raw/<snapshot>/` and `data/clean/<snapshot>/` (D19; rebuild with steps 00 → 01, and the committed manifests prove a match);
- INTERVIEW.md (private);
- `.venv/`.

**Deadline:** public link before the job application. Submit Sun 25 Oct night; hard stop Mon 26 Oct 09:00 IST.

**Resume — the commands** (run from this folder):

| to | run |
|---|---|
| set up env | `uv sync` |
| pull or verify raw snapshot | `uv run python 00_pull_data.py` |
| profile raw data | `uv run python 00b_profile.py` |
| clean + calendar + target/baselines | `uv run python 01_clean_target_atr.py` |
| regenerate FACTS.md | `uv run python facts.py` |
| tests | `uv run pytest -q` |
| test the tests | `uv run python -m tools.mutation_check` |
| refresh NSE holiday lists | `uv run python -m tools.fetch_nse_holidays --refresh` (see trap 6) |

**Open, in order of value:**
1. Chunk 2: Kronos smoke test, sampling trick and timing. Proposal in §8; waiting for "go".
2. Chunks 3–8.
3. After Chunk 8: India VIX baseline (D15).

**Schedule** (spec §8 with corrected weekdays; running about half a day late):

| day | chunks |
|---|---|
| Fri 23 Oct | 0–2 (0 and 1 done) |
| Sat 24 Oct | 2–7 |
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
- **GPU:** Kaggle free (T4/P100), about 30 h/week of quota, capped at 25 h (D16). There is no Kaggle CLI or API token on this Mac.

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
  FACTS.md                        GENERATED by facts.py, never hand-edited
  INTERVIEW.md                    problems → options → choice → why (gitignored, private)
  README.md                       public stub; full write-up in Chunk 8
  config.py                       every setting; rendered into FACTS.md (paths excluded)
  00_pull_data.py                 Yahoo → immutable snapshot + sha256 manifest; re-run = verify only
  00b_profile.py                  defects, gaps, volume quality → out/facts/00.json; prints real rows
  01_clean_target_atr.py          clean → official-calendar reconcile → TR%, ATR, naive → data/clean + out/facts/01.json
  facts.py                        out/facts/*.json + config → FACTS.md (checks the render is deterministic)
  lib/snapshot.py                 sha256; ensure/verify snapshot; load_raw (verified read); write_derived (atomic)
  lib/bars.py                     normalise raw rows; defect masks; gaps
  lib/clean.py                    the fixed cleaning order; stops on never-seen defect types
  lib/nse_calendar.py             official holidays + special/Muhurat tables → expected sessions, reconcile, scorable
  lib/features.py                 true range, Wilder ATR, tr_pct / atr_prev_pct / naive_prev_pct (one place each)
  lib/windows.py                  tune/test labels + release/overlap guards
  lib/facts.py                    fact records, group validation, Markdown render
  tools/fetch_nse_holidays.py     official NSE F&O holiday lists → data/calendar/nse_holidays_<year>.json
  tools/mutation_check.py         breaks the code on purpose; every mutation must fail a test
  tests/                          test_00_* (bars, snapshot, facts), test_01_* (features, clean, calendar)
  data/calendar/                  nse_holidays_2025/2026.json, special_sessions.csv, muhurat_sessions.csv (in git)
  data/raw/<snapshot>/            raw CSVs (not in git) + manifest.json (in git)
  data/clean/<snapshot>/          cleaned CSVs (not in git) + manifest.json with lineage hashes (in git)
  out/facts/                      per-step facts JSON (in git)
  pyproject.toml, uv.lock         pinned environment (dev: pytest, ta)
```

## 5. Chunk status
| chunk | scope | status |
|---|---|---|
| 0 | setup, pull and look at the data | done 2026-10-23 (FACTS step 00) |
| 1 | clean, calendar check, TR% target, ATR, naive | **done 2026-10-24** (FACTS step 01) |
| 2 | Kronos smoke test, sampling trick, timing | proposed (§8); waiting for "go" |
| 3 | samples → forecast | not started |
| 4 | metrics | not started |
| 5 | pre-register | not started |
| 6 | tune (Sep–Dec 2025) | not started |
| 7 | test once (2026) | not started |
| 8 | publish | not started |

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

### Chunk 2 — proposal (not started)
1. **Pin Kronos.** Clone `shiyu-coder/Kronos` at the commit in spec §4 and load Kronos-small and the tokenizer at the pinned Hugging Face revisions. Verify the commit and revisions exist first (playbook 1.6).
2. **Run locally first, on the M4 (MPS GPU, else CPU).**
   - Forecasting one bar takes one model pass per sample (estimate). The full plan may well fit on this Mac, which needs no action from the user during exams.
   - Measure the time per sample. If the full plan (tune grid + test + seeds) fits in a few hours, run it here. Otherwise use Kaggle, which needs a Kaggle API token from the user, or a manual notebook run.
   - This changes D18 to "Kaggle only if needed", to be recorded when decided.
3. **Smoke tests that could fail:**
   - `predict(sample_count=5)` returns one averaged row;
   - `predict_batch` with N copies returns N different rows (std > 0);
   - the `context_window(t)` assert fires on a window that contains *t*;
   - the same seed gives identical samples, and a different seed gives different ones;
   - timing is written to FACTS.
4. **No test-window outcomes** (D27). The smoke test runs on context-window days only, before 2025-09-01.
