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
# A new id makes a new snapshot. explore-2026-10-23 was used to build Chunks 0-2; the frozen pull (PREREG section 2)
# is made once, after PREREG.md is committed, and is the only snapshot tuning and test use.
SNAPSHOT_ID = "frozen-2026-10-24"
COMPARE_SNAPSHOT_ID = "explore-2026-10-23"  # step 01 diffs the frozen pull against it (Yahoo can revise history)
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

# --- Kronos (Chunk 2) ---
KRONOS_COMMIT = "67b630e67f6a18c9e9be918d9b4337c960db1e9a"  # vendor/Kronos submodule (spec section 4)
KRONOS_MODEL = "NeoQuasar/Kronos-small"
KRONOS_MODEL_REV = "901c26c1332695a2a8f243eb2f37243a37bea320"  # the revision upstream's regression test pins
KRONOS_MODEL_SHA256 = "b082dfcbd8e8c142a725c8bbb99781802f38fec81210e13479effb32b3c3e020"  # model.safetensors
KRONOS_TOKENIZER = "NeoQuasar/Kronos-Tokenizer-base"
KRONOS_TOKENIZER_REV = "0e0117387f39004a9016484a186a908917e22426"
KRONOS_TOKENIZER_SHA256 = "59d85f6af76a2c3b8240ea06cb21db4213b4eeca053f246b23e29cf832fc6bee"
KRONOS_MAX_CONTEXT = 512  # Kronos-small's limit
CONTEXT_DAYS = 400  # D3: rows strictly before day t fed to the model
TOP_K = 0  # off; only top_p filters (upstream default)
KRONOS_DEVICE = "cpu"  # D29: deterministic and portable; the fast sampler makes the GPU unnecessary

# --- Sampling (Chunks 2-3, 6-7) ---
N_SAMPLES = 5000  # D5 revised: samples per day; 5000 chosen in Chunk 2 from the timing (D30)
SEEDS = [1, 2, 3]  # per-day seeds derive from (seed, index, day); the first is the headline, the others the seed check (D12)
TUNE_GRID = [[0.6, 0.9], [0.6, 0.99], [0.8, 0.9], [0.8, 0.99], [1.0, 0.9], [1.0, 0.99]]  # D9: [temperature T, top_p]

# --- Scoring (Chunk 4) ---
BAND = [0.10, 0.90]  # D5: the band is the 10th-90th percentile, i.e. a central 80% interval
BOOT_N = 5000  # D10: moving-block bootstrap resamples
BOOT_BLOCK = 10  # D10: block length in trading days
BOOT_SEED = 7  # fixed, so the CI is reproducible
CI_LEVEL = 0.95
PASS_MAX_RATIO = 0.95  # D11: Kronos MAE / ATR MAE must be at most this...
PASS_CI_HIGH_BELOW = 1.00  # ...the CI's upper end strictly below this...
PASS_COVERAGE = [0.75, 0.85]  # ...and the calibrated band's coverage inside this range (ends included)

# --- Paths (not rendered in FACTS.md) ---
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
CALENDAR_DIR = ROOT / "data" / "calendar"
FACTS_DIR = ROOT / "out" / "facts"
SAMPLES_DIR = ROOT / "out" / "samples"  # cached Kronos samples, not in git
FACTS_MD = ROOT / "FACTS.md"
