"""Step 00: pull raw daily bars from Yahoo into an immutable, fingerprinted snapshot.

Re-running verifies the existing snapshot instead of downloading again. To pull fresh data,
set a new SNAPSHOT_ID in config.py.
"""
import yfinance as yf

import config
from lib.snapshot import ensure_snapshot


def fetch(symbol):
    yf.config.debug.hide_exceptions = config.YF_HIDE_EXCEPTIONS
    return yf.Ticker(symbol).history(start=config.HISTORY_START, **config.YF_HISTORY_KWARGS)


def main():
    meta = {
        "source": "Yahoo Finance via yfinance Ticker.history",
        "yfinance_version": yf.__version__,
        "history_start": config.HISTORY_START,
        "history_kwargs": config.YF_HISTORY_KWARGS,
        "hide_exceptions": config.YF_HIDE_EXCEPTIONS,
    }
    manifest, created = ensure_snapshot(config.RAW_DIR / config.SNAPSHOT_ID, config.TICKERS, fetch, meta)
    print(f"{'created' if created else 'verified existing'} snapshot {manifest['snapshot_id']} ({manifest['created_utc']} UTC)")
    for name, f in manifest["files"].items():
        print(f"  {name:<10} {f['symbol']:<9} {f['rows']:>5} rows  sha256 {f['sha256'][:16]}…")


if __name__ == "__main__":
    main()
