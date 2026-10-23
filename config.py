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

# --- Calendar, cleaning, target, baselines (Chunk 1) ---
ATR_PERIOD = 14  # Wilder ATR(14), the chart indicator (D7, decision iii)
KRONOS_RELEASE = "2025-08-02"  # arXiv 2508.02739 v1; every tuning and test day must come after it (ground rule 2)
TUNE_START = "2025-09-01"
TUNE_END = "2025-12-31"
TEST_START = "2026-01-01"  # the test window runs to the last complete day in the snapshot
CALENDAR_START = "2025-08-01"  # official NSE calendar coverage starts here; all scored days fall inside it
HOLIDAY_YEARS = [2025, 2026]  # years of the official NSE F&O holiday list kept in data/calendar/

# --- Paths (not rendered in FACTS.md) ---
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
CALENDAR_DIR = ROOT / "data" / "calendar"
FACTS_DIR = ROOT / "out" / "facts"
FACTS_MD = ROOT / "FACTS.md"
