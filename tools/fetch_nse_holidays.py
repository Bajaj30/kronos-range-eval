"""Save NSE's official F&O trading-holiday list for each year in config.HOLIDAY_YEARS.

Writes data/calendar/nse_holidays_<year>.json (only the F&O segment, descriptions stripped) with the
source URL and retrieval time. The files are public calendar facts, not market data, so they are committed.

  uv run python -m tools.fetch_nse_holidays                   fetch years not yet saved
  uv run python -m tools.fetch_nse_holidays --refresh         fetch all years again
  uv run python -m tools.fetch_nse_holidays --from-dir DIR    build from saved API responses
                                                              DIR/nse_trading_<year>.json (e.g. saved with curl)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import config

API = "https://www.nseindia.com/api/holiday-master"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36",
    "Referer": "https://www.nseindia.com/resources/exchange-communication-holidays",
    "Accept": "application/json",
}


def parse_fo(response: dict, year: int) -> list[dict]:
    """The F&O segment of one holiday-master response -> [{date, weekday, description}], checked for the year."""
    rows = [
        {"date": datetime.strptime(x["tradingDate"], "%d-%b-%Y").date().isoformat(),
         "weekday": x["weekDay"].strip(), "description": x["description"].strip()}
        for x in response["FO"]
    ]
    wrong_year = [x["date"] for x in rows if not x["date"].startswith(str(year))]
    if not rows or wrong_year:
        raise RuntimeError(f"{year}: unexpected response (rows={len(rows)}, other years: {wrong_year[:3]})")
    return rows


def fetch(year: int, session) -> tuple[dict, str]:
    r = session.get(API, params={"type": "trading", "year": year}, timeout=20)
    r.raise_for_status()
    return r.json(), datetime.now(timezone.utc).isoformat(timespec="seconds")


def from_file(year: int, folder: Path) -> tuple[dict, str]:
    path = folder / f"nse_trading_{year}.json"
    retrieved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
    return json.loads(path.read_text()), retrieved


def main(argv: list[str]):
    refresh = "--refresh" in argv
    folder = Path(argv[argv.index("--from-dir") + 1]) if "--from-dir" in argv else None
    session = None
    for year in config.HOLIDAY_YEARS:
        out = config.CALENDAR_DIR / f"nse_holidays_{year}.json"
        if out.exists() and not refresh:
            print(f"{year}: kept existing {out.name}")
            continue
        if folder is not None:
            response, retrieved = from_file(year, folder)
        else:
            if session is None:
                import requests

                session = requests.Session()
                session.headers.update(HEADERS)
                session.get("https://www.nseindia.com/", timeout=20)  # sets the cookies the API needs (may be 403)
            response, retrieved = fetch(year, session)
        rows = parse_fo(response, year)
        doc = {"source_url": f"{API}?type=trading&year={year}", "segment": "FO", "retrieved_utc": retrieved,
               "holidays": rows}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"{year}: saved {len(rows)} entries to {out.name} (retrieved {retrieved})")


if __name__ == "__main__":
    main(sys.argv[1:])
