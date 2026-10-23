# FACTS — generated, never hand-edited

> Every number used in chat, the README, the resume or the site comes from this file.
> Regenerate: `uv run python facts.py`. Inputs: `config.py` and `out/facts/*.json`.

## Groups (what each number describes)

| group | meaning |
|---|---|
| CONFIG | settings in `config.py` |
| RAW-BANKNIFTY | BANKNIFTY (^NSEBANK) daily rows exactly as received in snapshot explore-2026-10-23 |
| RAW-NIFTY | NIFTY (^NSEI) daily rows exactly as received in snapshot explore-2026-10-23 |
| SNAPSHOT | snapshot explore-2026-10-23 as a whole |

## Settings (group: CONFIG)

| setting | value |
|---|---|
| TICKERS | `{"BANKNIFTY": "^NSEBANK", "NIFTY": "^NSEI"}` |
| HISTORY_START | 2015-01-01 |
| YF_HISTORY_KWARGS | `{"actions": true, "auto_adjust": false, "interval": "1d", "keepna": true}` |
| YF_HIDE_EXCEPTIONS | False |
| SNAPSHOT_ID | explore-2026-10-23 |
| MARKET_TZ | Asia/Kolkata |
| GAP_DAYS | 5 |
| SPIKE_PCT | 20 |

## Step 00 — Raw data profile

Source: `00b_profile.py`

| group | key | value | meaning |
|---|---|---|---|
| SNAPSHOT | snapshot_id | explore-2026-10-23 | snapshot id |
| SNAPSHOT | created_utc | 2026-10-23T13:31:27+00:00 | when the pull finished (UTC) |
| SNAPSHOT | pull_day_ist | 2026-10-23 | pull date in market time; bars on this date may be unfinished |
| SNAPSHOT | yfinance_version | 1.7.0 | yfinance version used for the pull |
| SNAPSHOT | sha256_BANKNIFTY | 60ad50a802871a66e3a62abc2e40422fe3c9dbe637b92d30d47b1992ddb526a7 | sha256 of BANKNIFTY.csv |
| SNAPSHOT | sha256_NIFTY | 64c011af0ccc78bcae33c5f867819d604598a308a78fd90fc35fc41efae7c316 | sha256 of NIFTY.csv |
| RAW-NIFTY | rows | 2916 | rows as received |
| RAW-NIFTY | first_date | 2015-01-02 | first bar date |
| RAW-NIFTY | last_date | 2026-10-23 | last bar date |
| RAW-NIFTY | defect_missing_price | 9 | rows flagged missing_price |
| RAW-NIFTY | defect_duplicate_date | 0 | rows flagged duplicate_date |
| RAW-NIFTY | defect_out_of_order | 0 | rows flagged out_of_order |
| RAW-NIFTY | defect_flat_bar | 0 | rows flagged flat_bar |
| RAW-NIFTY | defect_high_below_body | 0 | rows flagged high_below_body |
| RAW-NIFTY | defect_low_above_body | 0 | rows flagged low_above_body |
| RAW-NIFTY | defect_nonpositive_price | 0 | rows flagged nonpositive_price |
| RAW-NIFTY | defect_price_spike | 0 | rows flagged price_spike |
| RAW-NIFTY | defect_not_midnight | 0 | rows flagged not_midnight |
| RAW-NIFTY | defect_on_or_after_pull_day | 1 | rows flagged on_or_after_pull_day |
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
| RAW-BANKNIFTY | defect_missing_price | 5 | rows flagged missing_price |
| RAW-BANKNIFTY | defect_duplicate_date | 0 | rows flagged duplicate_date |
| RAW-BANKNIFTY | defect_out_of_order | 0 | rows flagged out_of_order |
| RAW-BANKNIFTY | defect_flat_bar | 1 | rows flagged flat_bar |
| RAW-BANKNIFTY | defect_high_below_body | 0 | rows flagged high_below_body |
| RAW-BANKNIFTY | defect_low_above_body | 0 | rows flagged low_above_body |
| RAW-BANKNIFTY | defect_nonpositive_price | 0 | rows flagged nonpositive_price |
| RAW-BANKNIFTY | defect_price_spike | 0 | rows flagged price_spike |
| RAW-BANKNIFTY | defect_not_midnight | 0 | rows flagged not_midnight |
| RAW-BANKNIFTY | defect_on_or_after_pull_day | 1 | rows flagged on_or_after_pull_day |
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
| 2026-10-23 | Fri | on_or_after_pull_day |

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
| 2026-10-23 | Fri | on_or_after_pull_day |

**Dates present in only one index** (group: SNAPSHOT)

| date | only in |
|---|---|
| 2015-01-01 | BANKNIFTY |
