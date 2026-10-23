# FACTS — generated, never hand-edited

> Every number used in chat, the README, the resume or the site comes from this file.
> Regenerate: `uv run python facts.py`. Inputs: `config.py` and `out/facts/*.json`.

## Groups (what each number describes)

| group | meaning |
|---|---|
| CONFIG | settings in `config.py` |
| CALENDAR | official NSE session calendar check, 2025-08-01 to 2026-10-23 |
| CLEAN-BANKNIFTY | BANKNIFTY rows after cleaning, snapshot frozen-2026-10-24 |
| CLEAN-NIFTY | NIFTY rows after cleaning, snapshot frozen-2026-10-24 |
| RAW-BANKNIFTY | BANKNIFTY (^NSEBANK) daily rows exactly as received in snapshot frozen-2026-10-24 |
| RAW-NIFTY | NIFTY (^NSEI) daily rows exactly as received in snapshot frozen-2026-10-24 |
| REVISIONS | raw rows of snapshot frozen-2026-10-24 compared with the same dates in explore-2026-10-23 |
| SMOKE | Kronos-small smoke test on NIFTY, the 5 days before 2025-09-01 (2025-08-22 to 2025-08-29); T=1.0, top_p=0.9 |
| SNAPSHOT | snapshot frozen-2026-10-24 as a whole |
| TEST-BANKNIFTY | BANKNIFTY days in the test window 2026-01-01 to 2026-10-23 |
| TEST-NIFTY | NIFTY days in the test window 2026-01-01 to 2026-10-23 |
| TIMING | wall-clock on this machine, device=cpu, torch 2.14.1, 4 threads (a measurement: varies run to run) |
| TUNE-BANKNIFTY | BANKNIFTY days in the tuning window 2025-09-01 to 2025-12-31 |
| TUNE-NIFTY | NIFTY days in the tuning window 2025-09-01 to 2025-12-31 |

## Settings (group: CONFIG)

| setting | value |
|---|---|
| TICKERS | `{"BANKNIFTY": "^NSEBANK", "NIFTY": "^NSEI"}` |
| HISTORY_START | 2015-01-01 |
| YF_HISTORY_KWARGS | `{"actions": true, "auto_adjust": false, "interval": "1d", "keepna": true}` |
| YF_HIDE_EXCEPTIONS | False |
| SNAPSHOT_ID | frozen-2026-10-24 |
| COMPARE_SNAPSHOT_ID | explore-2026-10-23 |
| MARKET_TZ | Asia/Kolkata |
| GAP_DAYS | 5 |
| SPIKE_PCT | 20 |
| ATR_PERIOD | 14 |
| KRONOS_RELEASE | 2025-08-02 |
| TUNE_START | 2025-09-01 |
| TUNE_END | 2025-12-31 |
| TEST_START | 2026-01-01 |
| CALENDAR_START | 2025-08-01 |
| HOLIDAY_YEARS | `[2025, 2026]` |
| KRONOS_COMMIT | 67b630e67f6a18c9e9be918d9b4337c960db1e9a |
| KRONOS_MODEL | NeoQuasar/Kronos-small |
| KRONOS_MODEL_REV | 901c26c1332695a2a8f243eb2f37243a37bea320 |
| KRONOS_MODEL_SHA256 | b082dfcbd8e8c142a725c8bbb99781802f38fec81210e13479effb32b3c3e020 |
| KRONOS_TOKENIZER | NeoQuasar/Kronos-Tokenizer-base |
| KRONOS_TOKENIZER_REV | 0e0117387f39004a9016484a186a908917e22426 |
| KRONOS_TOKENIZER_SHA256 | 59d85f6af76a2c3b8240ea06cb21db4213b4eeca053f246b23e29cf832fc6bee |
| KRONOS_MAX_CONTEXT | 512 |
| CONTEXT_DAYS | 400 |
| TOP_K | 0 |
| KRONOS_DEVICE | cpu |
| N_SAMPLES | 5000 |
| SEEDS | `[1, 2, 3]` |
| TUNE_GRID | `[[0.6, 0.9], [0.6, 0.99], [0.8, 0.9], [0.8, 0.99], [1.0, 0.9], [1.0, 0.99]]` |
| BAND | `[0.1, 0.9]` |
| BOOT_N | 5000 |
| BOOT_BLOCK | 10 |
| BOOT_SEED | 7 |
| CI_LEVEL | 0.95 |
| PASS_MAX_RATIO | 0.95 |
| PASS_CI_HIGH_BELOW | 1 |
| PASS_COVERAGE | `[0.75, 0.85]` |

## Step 00 — Raw data profile

Source: `00b_profile.py`

| group | key | value | meaning |
|---|---|---|---|
| SNAPSHOT | snapshot_id | frozen-2026-10-24 | snapshot id |
| SNAPSHOT | created_utc | 2026-10-23T23:10:06+00:00 | when the pull finished (UTC) |
| SNAPSHOT | pull_day_ist | 2026-10-24 | pull date in market time; bars on this date may be unfinished |
| SNAPSHOT | yfinance_version | 1.7.0 | yfinance version used for the pull |
| SNAPSHOT | sha256_BANKNIFTY | 59955330f6167c3d81bb0daf91ba08472ca227412508e7db64addeff15cb8ed4 | sha256 of BANKNIFTY.csv |
| SNAPSHOT | sha256_NIFTY | 74da4453bad563f82a9ab540d0eccab3ce038f79f0eb560d70d676c8a03f5720 | sha256 of NIFTY.csv |
| RAW-NIFTY | rows | 2916 | rows as received |
| RAW-NIFTY | first_date | 2015-01-02 | first bar date |
| RAW-NIFTY | last_date | 2026-10-23 | last bar date |
| RAW-NIFTY | defect_missing_price | 10 | rows flagged missing_price |
| RAW-NIFTY | defect_duplicate_date | 0 | rows flagged duplicate_date |
| RAW-NIFTY | defect_out_of_order | 0 | rows flagged out_of_order |
| RAW-NIFTY | defect_flat_bar | 0 | rows flagged flat_bar |
| RAW-NIFTY | defect_high_below_body | 0 | rows flagged high_below_body |
| RAW-NIFTY | defect_low_above_body | 0 | rows flagged low_above_body |
| RAW-NIFTY | defect_nonpositive_price | 0 | rows flagged nonpositive_price |
| RAW-NIFTY | defect_price_spike | 0 | rows flagged price_spike |
| RAW-NIFTY | defect_not_midnight | 0 | rows flagged not_midnight |
| RAW-NIFTY | defect_on_or_after_pull_day | 0 | rows flagged on_or_after_pull_day |
| RAW-NIFTY | rows_with_any_defect | 10 | rows with at least one defect |
| RAW-NIFTY | rows_without_defect | 2906 | rows with no defect |
| RAW-NIFTY | gaps_over_threshold | 0 | consecutive rows more than 5 calendar days apart |
| RAW-NIFTY | weekend_rows | 4 | rows dated Saturday or Sunday (special sessions?) |
| RAW-NIFTY | volume_zero_rows | 38 | rows with volume exactly 0 |
| RAW-NIFTY | volume_nan_rows | 0 | rows with volume missing |
| RAW-NIFTY | volume_positive_rows | 2878 | rows with volume > 0 |
| RAW-NIFTY | volume_first_positive | 2015-01-02 | first date with volume > 0 |
| RAW-NIFTY | volume_last_zero | 2026-10-23 | last date with volume 0 |
| RAW-NIFTY | adj_close_max_rel_diff | 0 | largest \|Adj Close - Close\| / Close where both exist (Adj Close is not used) |
| RAW-NIFTY | dividend_rows | 0 | rows with a non-zero dividend (expected 0) |
| RAW-NIFTY | split_rows | 0 | rows with a non-zero split (expected 0) |
| RAW-BANKNIFTY | rows | 2917 | rows as received |
| RAW-BANKNIFTY | first_date | 2015-01-01 | first bar date |
| RAW-BANKNIFTY | last_date | 2026-10-23 | last bar date |
| RAW-BANKNIFTY | defect_missing_price | 6 | rows flagged missing_price |
| RAW-BANKNIFTY | defect_duplicate_date | 0 | rows flagged duplicate_date |
| RAW-BANKNIFTY | defect_out_of_order | 0 | rows flagged out_of_order |
| RAW-BANKNIFTY | defect_flat_bar | 1 | rows flagged flat_bar |
| RAW-BANKNIFTY | defect_high_below_body | 0 | rows flagged high_below_body |
| RAW-BANKNIFTY | defect_low_above_body | 0 | rows flagged low_above_body |
| RAW-BANKNIFTY | defect_nonpositive_price | 0 | rows flagged nonpositive_price |
| RAW-BANKNIFTY | defect_price_spike | 0 | rows flagged price_spike |
| RAW-BANKNIFTY | defect_not_midnight | 0 | rows flagged not_midnight |
| RAW-BANKNIFTY | defect_on_or_after_pull_day | 0 | rows flagged on_or_after_pull_day |
| RAW-BANKNIFTY | rows_with_any_defect | 7 | rows with at least one defect |
| RAW-BANKNIFTY | rows_without_defect | 2910 | rows with no defect |
| RAW-BANKNIFTY | gaps_over_threshold | 0 | consecutive rows more than 5 calendar days apart |
| RAW-BANKNIFTY | weekend_rows | 4 | rows dated Saturday or Sunday (special sessions?) |
| RAW-BANKNIFTY | volume_zero_rows | 1112 | rows with volume exactly 0 |
| RAW-BANKNIFTY | volume_nan_rows | 0 | rows with volume missing |
| RAW-BANKNIFTY | volume_positive_rows | 1805 | rows with volume > 0 |
| RAW-BANKNIFTY | volume_first_positive | 2015-01-01 | first date with volume > 0 |
| RAW-BANKNIFTY | volume_last_zero | 2026-10-23 | last date with volume 0 |
| RAW-BANKNIFTY | adj_close_max_rel_diff | 1.168e-05 | largest \|Adj Close - Close\| / Close where both exist (Adj Close is not used) |
| RAW-BANKNIFTY | dividend_rows | 0 | rows with a non-zero dividend (expected 0) |
| RAW-BANKNIFTY | split_rows | 0 | rows with a non-zero split (expected 0) |
| SNAPSHOT | dates_only_in_NIFTY | 0 | dates present in NIFTY but not BANKNIFTY |
| SNAPSHOT | dates_only_in_BANKNIFTY | 1 | dates present in BANKNIFTY but not NIFTY |

**NIFTY: rows per calendar year** (group: RAW-NIFTY)

| year | rows | zero-volume rows |
|---|---|---|
| 2015 | 246 | 2 |
| 2016 | 246 | 2 |
| 2017 | 248 | 1 |
| 2018 | 246 | 14 |
| 2019 | 243 | 2 |
| 2020 | 251 | 3 |
| 2021 | 248 | 4 |
| 2022 | 248 | 1 |
| 2023 | 245 | 2 |
| 2024 | 246 | 5 |
| 2025 | 249 | 0 |
| 2026 | 200 | 2 |

**NIFTY: 10 lowest-volume rows (volume > 0, no defect)** (group: RAW-NIFTY)

| date | weekday | volume | (high-low)/open % |
|---|---|---|---|
| 2017-07-10 | Mon | 37500 | 1.4 |
| 2017-10-19 | Thu | 30200 | 0.87 |
| 2018-11-07 | Wed | 31200 | 0.32 |
| 2020-01-21 | Tue | 400 | 0.56 |
| 2020-01-22 | Wed | 500 | 1.12 |
| 2021-03-16 | Tue | 100 | 1.07 |
| 2021-03-17 | Wed | 100 | 1.74 |
| 2024-11-01 | Fri | 38800 | 0.36 |
| 2025-10-21 | Tue | 42500 | 0.42 |
| 2025-11-03 | Mon | 23300 | 0.61 |

**NIFTY: every flagged or weekend row** (group: RAW-NIFTY)

| date | weekday | defects |
|---|---|---|
| 2015-02-28 | Sat | missing_price |
| 2015-04-15 | Wed | missing_price |
| 2016-01-01 | Fri | missing_price |
| 2016-08-12 | Fri | missing_price |
| 2018-01-01 | Mon | missing_price |
| 2019-01-01 | Tue | missing_price |
| 2019-10-27 | Sun | missing_price |
| 2020-11-14 | Sat | missing_price |
| 2025-02-01 | Sat | weekend only |
| 2026-01-15 | Thu | missing_price |
| 2026-10-23 | Fri | missing_price |

**BANKNIFTY: rows per calendar year** (group: RAW-BANKNIFTY)

| year | rows | zero-volume rows |
|---|---|---|
| 2015 | 247 | 190 |
| 2016 | 246 | 11 |
| 2017 | 248 | 244 |
| 2018 | 246 | 233 |
| 2019 | 243 | 190 |
| 2020 | 251 | 99 |
| 2021 | 248 | 136 |
| 2022 | 248 | 1 |
| 2023 | 245 | 2 |
| 2024 | 246 | 3 |
| 2025 | 249 | 1 |
| 2026 | 200 | 2 |

**BANKNIFTY: 10 lowest-volume rows (volume > 0, no defect)** (group: RAW-BANKNIFTY)

| date | weekday | volume | (high-low)/open % |
|---|---|---|---|
| 2015-01-01 | Thu | 20500 | 0.76 |
| 2015-12-07 | Mon | 34900 | 0.65 |
| 2015-12-23 | Wed | 37200 | 0.6 |
| 2015-12-24 | Thu | 27100 | 1.08 |
| 2015-12-29 | Tue | 36300 | 0.73 |
| 2016-01-01 | Fri | 29200 | 1.44 |
| 2018-11-07 | Wed | 1800 | 0.3 |
| 2025-04-21 | Mon | 300 | 1.43 |
| 2025-11-03 | Mon | 27800 | 0.92 |
| 2026-02-05 | Thu | 200 | 0.74 |

**BANKNIFTY: every flagged or weekend row** (group: RAW-BANKNIFTY)

| date | weekday | defects |
|---|---|---|
| 2015-02-28 | Sat | missing_price |
| 2016-11-10 | Thu | flat_bar |
| 2019-10-27 | Sun | missing_price |
| 2020-11-14 | Sat | missing_price |
| 2025-02-01 | Sat | missing_price |
| 2026-01-15 | Thu | missing_price |
| 2026-10-23 | Fri | missing_price |

**Dates present in only one index** (group: SNAPSHOT)

| date | only in |
|---|---|
| 2015-01-01 | BANKNIFTY |

## Step 01 — Clean, calendar check, target and baselines

Source: `01_clean_target_atr.py`

| group | key | value | meaning |
|---|---|---|---|
| CALENDAR | expected_sessions | 302 | sessions that should have a daily bar |
| CALENDAR | muhurat_dates_listed | 11 | Muhurat dates in muhurat_sessions.csv |
| CALENDAR | muhurat_closes_matched | 6 | Muhurat dates whose NIFTY row equals the published Muhurat close |
| CLEAN-NIFTY | dropped_pull_day_or_later | 0 | rows removed: pull_day_or_later (cleaning step 1) |
| CLEAN-NIFTY | dropped_missing_price | 10 | rows removed: missing_price (cleaning step 2) |
| CLEAN-NIFTY | dropped_muhurat_session | 6 | rows removed: muhurat_session (cleaning step 3) |
| CLEAN-NIFTY | dropped_impossible_bar | 0 | rows removed: impossible_bar (cleaning step 4) |
| CLEAN-NIFTY | rows | 2900 | rows kept |
| CLEAN-NIFTY | first_date | 2015-01-02 | first kept date |
| CLEAN-NIFTY | last_date | 2026-10-22 | last kept date (last complete day) |
| CLEAN-NIFTY | atr_parity_max_rel_diff | 7.162e-16 | largest relative gap between our ATR(14) and the ta library's, tuning + test rows |
| CALENDAR | missing_sessions_NIFTY | 2 | NIFTY: official sessions with no bar in the data |
| CALENDAR | extra_rows_NIFTY | 0 | NIFTY: bars on dates that are not sessions |
| TUNE-NIFTY | rows | 83 | rows in the window |
| TUNE-NIFTY | scorable_days | 83 | days that will be scored (the n of every metric) |
| TUNE-NIFTY | unscorable_days | 0 | days in the window that are not scored |
| TEST-NIFTY | rows | 198 | rows in the window |
| TEST-NIFTY | scorable_days | 197 | days that will be scored (the n of every metric) |
| TEST-NIFTY | unscorable_days | 1 | days in the window that are not scored |
| CLEAN-BANKNIFTY | dropped_pull_day_or_later | 0 | rows removed: pull_day_or_later (cleaning step 1) |
| CLEAN-BANKNIFTY | dropped_missing_price | 6 | rows removed: missing_price (cleaning step 2) |
| CLEAN-BANKNIFTY | dropped_muhurat_session | 6 | rows removed: muhurat_session (cleaning step 3) |
| CLEAN-BANKNIFTY | dropped_impossible_bar | 1 | rows removed: impossible_bar (cleaning step 4) |
| CLEAN-BANKNIFTY | rows | 2904 | rows kept |
| CLEAN-BANKNIFTY | first_date | 2015-01-01 | first kept date |
| CLEAN-BANKNIFTY | last_date | 2026-10-22 | last kept date (last complete day) |
| CLEAN-BANKNIFTY | atr_parity_max_rel_diff | 6.809e-16 | largest relative gap between our ATR(14) and the ta library's, tuning + test rows |
| CALENDAR | missing_sessions_BANKNIFTY | 2 | BANKNIFTY: official sessions with no bar in the data |
| CALENDAR | extra_rows_BANKNIFTY | 0 | BANKNIFTY: bars on dates that are not sessions |
| TUNE-BANKNIFTY | rows | 83 | rows in the window |
| TUNE-BANKNIFTY | scorable_days | 83 | days that will be scored (the n of every metric) |
| TUNE-BANKNIFTY | unscorable_days | 0 | days in the window that are not scored |
| TEST-BANKNIFTY | rows | 198 | rows in the window |
| TEST-BANKNIFTY | scorable_days | 197 | days that will be scored (the n of every metric) |
| TEST-BANKNIFTY | unscorable_days | 1 | days in the window that are not scored |
| REVISIONS | NIFTY_common_rows | 2916 | NIFTY: dates in both snapshots |
| REVISIONS | NIFTY_changed_rows | 1 | NIFTY: common dates whose O/H/L/C differ (incl. missing) |
| REVISIONS | NIFTY_rows_now_missing_a_price | 1 | NIFTY: common dates where a price present before is missing now |
| REVISIONS | NIFTY_max_rel_change | 0 | NIFTY: largest relative change where both snapshots have the price |
| REVISIONS | NIFTY_new_rows | 0 | NIFTY: dates only in the new snapshot |
| REVISIONS | BANKNIFTY_common_rows | 2917 | BANKNIFTY: dates in both snapshots |
| REVISIONS | BANKNIFTY_changed_rows | 1 | BANKNIFTY: common dates whose O/H/L/C differ (incl. missing) |
| REVISIONS | BANKNIFTY_rows_now_missing_a_price | 1 | BANKNIFTY: common dates where a price present before is missing now |
| REVISIONS | BANKNIFTY_max_rel_change | 0 | BANKNIFTY: largest relative change where both snapshots have the price |
| REVISIONS | BANKNIFTY_new_rows | 0 | BANKNIFTY: dates only in the new snapshot |
| CALENDAR | clean_sha256_BANKNIFTY | e45dd305e358aa3be3ea6487f7a63c97eeef580c28c4d9ebfe96859de87ea9e9 | sha256 of the cleaned BANKNIFTY.csv |
| CALENDAR | clean_sha256_NIFTY | b9f05e7f000fc562c3871d6998daf6815ab3eb57770024de09b02716b323b3e5 | sha256 of the cleaned NIFTY.csv |

**Muhurat dates checked against published closes** (group: CALENDAR)

| date | published NIFTY close | Yahoo close | match |
|---|---|---|---|
| 2016-10-30 | 8625.70 | no row or no price | n/a |
| 2017-10-19 | 10146.55 | 10146.55 | yes |
| 2018-11-07 | 10598.40 | 10598.40 | yes |
| 2019-10-27 | 11627.15 | no row or no price | n/a |
| 2020-11-14 | 12780.25 | no row or no price | n/a |
| 2021-11-04 | 17916.80 | 17916.80 | yes |
| 2022-10-24 | 17730.75 | 17730.75 | yes |
| 2023-11-12 | 19525.55 | no row or no price | n/a |
| 2024-11-01 | 24304.35 | 24304.35 | yes |
| 2025-10-21 | 25868.60 | 25868.60 | yes |
| 2026-11-08 | — | no row or no price | n/a |

**NIFTY test: days not scored** (group: TEST-NIFTY)

| date | weekday | why |
|---|---|---|
| 2026-02-02 | Mon | previous session missing from the data |

**NIFTY: official sessions missing from the data** (group: CALENDAR)

| date | weekday | effect |
|---|---|---|
| 2026-02-01 | Sun | next session is not scored |
| 2026-10-23 | Fri | next session is not scored |

**NIFTY: rows removed by cleaning** (group: CLEAN-NIFTY)

| date | weekday | reason |
|---|---|---|
| 2015-02-28 | Sat | missing price |
| 2015-04-15 | Wed | missing price |
| 2016-01-01 | Fri | missing price |
| 2016-08-12 | Fri | missing price |
| 2017-10-19 | Thu | Muhurat session |
| 2018-01-01 | Mon | missing price |
| 2018-11-07 | Wed | Muhurat session |
| 2019-01-01 | Tue | missing price |
| 2019-10-27 | Sun | missing price |
| 2020-11-14 | Sat | missing price |
| 2021-11-04 | Thu | Muhurat session |
| 2022-10-24 | Mon | Muhurat session |
| 2024-11-01 | Fri | Muhurat session |
| 2025-10-21 | Tue | Muhurat session |
| 2026-01-15 | Thu | missing price |
| 2026-10-23 | Fri | missing price |

**BANKNIFTY test: days not scored** (group: TEST-BANKNIFTY)

| date | weekday | why |
|---|---|---|
| 2026-02-02 | Mon | previous session missing from the data |

**BANKNIFTY: official sessions missing from the data** (group: CALENDAR)

| date | weekday | effect |
|---|---|---|
| 2026-02-01 | Sun | next session is not scored |
| 2026-10-23 | Fri | next session is not scored |

**BANKNIFTY: rows removed by cleaning** (group: CLEAN-BANKNIFTY)

| date | weekday | reason |
|---|---|---|
| 2015-02-28 | Sat | missing price |
| 2016-11-10 | Thu | impossible bar |
| 2017-10-19 | Thu | Muhurat session |
| 2018-11-07 | Wed | Muhurat session |
| 2019-10-27 | Sun | missing price |
| 2020-11-14 | Sat | missing price |
| 2021-11-04 | Thu | Muhurat session |
| 2022-10-24 | Mon | Muhurat session |
| 2024-11-01 | Fri | Muhurat session |
| 2025-02-01 | Sat | missing price |
| 2025-10-21 | Tue | Muhurat session |
| 2026-01-15 | Thu | missing price |
| 2026-10-23 | Fri | missing price |

**Revised rows (first 10 per index)** (group: REVISIONS)

| index | date | change |
|---|---|---|
| NIFTY | 2026-10-23 | close: 22600.00 → missing |
| BANKNIFTY | 2026-10-23 | close: 54287.35 → missing |

## Step 02 — Kronos smoke test, sampler parity and timing

Source: `02_kronos_smoke.py`

| group | key | value | meaning |
|---|---|---|---|
| SMOKE | kronos_commit | 67b630e67f6a18c9e9be918d9b4337c960db1e9a | vendor/Kronos HEAD, equal to the pin, no local edits |
| SMOKE | weights_sha256_verified | yes | model and tokenizer safetensors match the pinned sha256 |
| SMOKE | upstream_regression_tests_passed | 4 | Kronos's own regression tests (pinned revisions, greedy decoding) passing in this environment |
| SMOKE | rows_from_predict_sample_count_5 | 1 | upstream predict(sample_count=5) returns ONE averaged row |
| SMOKE | parity_samples_compared | 2500 | 500 samples x 5 days, same seeds |
| SMOKE | parity_samples_identical | 2500 | fast sampler == upstream predict_batch on copies, bit for bit |
| SMOKE | same_seed_identical | True | rerun with the same seed gives identical samples |
| SMOKE | new_seed_differs | True | a different seed gives different samples |
| SMOKE | n_samples | 5000 | samples per day (production count, D5) |
| SMOKE | median_distinct_tr_values | 16 | distinct TR% values among the samples of a day, median over the smoke days (outputs are tokens) |
| TIMING | fast_seconds_per_day | 0.2561 | fast sampler, 5000 samples, median over days |
| TIMING | upstream_ms_per_sample | 41.81 | upstream predict_batch on 500 copies |
| TIMING | planned_day_runs | 2178 | 6 configs x tune days + 3 seeds x test days, both indices |
| TIMING | planned_minutes_fast_estimate | 9.297 | estimate: day runs x fast seconds per day |
| TIMING | planned_hours_upstream_estimate | 126.5 | estimate: the same plan through upstream copies |

**First look: raw (uncalibrated) forecasts vs the actual true range, % of previous close** (group: SMOKE)

| date | day | actual TR% | ATR(14)% | naive% | Kronos median% | Kronos 10–90% | distinct sample values |
|---|---|---|---|---|---|---|---|
| 2025-08-22 | Fri | 0.900 | 0.793 | 0.412 | 0.777 | 0.634 – 1.117 | 18 |
| 2025-08-25 | Mon | 0.609 | 0.808 | 0.900 | 0.820 | 0.552 – 0.975 | 14 |
| 2025-08-26 | Tue | 1.114 | 0.791 | 0.609 | 0.794 | 0.537 – 0.879 | 10 |
| 2025-08-28 | Thu | 0.933 | 0.822 | 1.114 | 0.831 | 0.667 – 1.110 | 16 |
| 2025-08-29 | Fri | 0.685 | 0.837 | 0.933 | 0.918 | 0.799 – 1.179 | 27 |
