# Kronos vs ATR: next-day NIFTY range forecast test

**Work in progress (v1).** Does a pre-trained time-series foundation model ([Kronos](https://github.com/shiyu-coder/Kronos)) forecast tomorrow's NIFTY 50 trading range better than the classic ATR(14) rule, on days after the model was released?

- Settings are pre-registered before a single test run.
- Every number comes from the generated [FACTS.md](FACTS.md).
- The method, results and limits will be published here when the test is done.

**Status:**
- Data pipeline done: pull, profile, cleaning, reconciliation against NSE's official trading calendar, target and ATR/naive baselines.
- Kronos sampling done and checked bit for bit against the upstream implementation; metrics done.
- **Pre-registered:** [PREREG.md](PREREG.md) fixes every setting and the pass rule before any tuning or test output exists.
- Next: tuning on Sep–Dec 2025, then one test run on 2026.

Raw market data is not redistributed in this repo. `00_pull_data.py` rebuilds it, and the committed manifest's sha256 shows whether your pull matches.
