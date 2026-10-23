"""Every setting for v1 lives here. FACTS.md renders these values; PREREG.md (Chunk 5) mirrors them."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# --- Data source (Chunk 0) ---
TICKERS = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}  # name -> Yahoo symbol
HISTORY_START = "2015-01-01"
# keepna=True: keep rows Yahoo returns with missing prices, so we can count them instead of losing them silently.
YF_HISTORY_KWARGS = {"interval": "1d", "auto_adjust": False, "actions": True, "keepna": True}
# yfinance hides download errors by default and returns an empty table; False makes them raise.
YF_HIDE_EXCEPTIONS = False
SNAPSHOT_ID = "explore-2026-10-23"  # a new id makes a new snapshot; the Chunk 6 frozen pull gets its own id
MARKET_TZ = "Asia/Kolkata"

# --- Profiling thresholds (Chunk 0) ---
GAP_DAYS = 5  # consecutive rows more than this many calendar days apart count as a gap
SPIKE_PCT = 20.0  # an O/H/L/C this far (%) from the previous close is treated as a bad print

# --- Paths (not rendered in FACTS.md) ---
RAW_DIR = ROOT / "data" / "raw"
FACTS_DIR = ROOT / "out" / "facts"
FACTS_MD = ROOT / "FACTS.md"
