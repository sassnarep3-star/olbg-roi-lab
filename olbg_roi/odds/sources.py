"""Odds ingestion adapters.

Primary path: The Odds API (free tier, key via ODDS_API_KEY env var) —
https://the-odds-api.com — aggregates bookmaker odds for most sports here.

OLBG itself is an odds-comparison + tips site with no official public API.
Scraping it may violate its terms of service, so by default we point users to
the same bookmaker feeds OLBG compares, and we keep an adapter stub here so we
can wire in OLBG-derived data (e.g. a CSV export of odds/tips) when available.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import Market

# The Odds API sport keys (https://the-odds-api.com/sports-odds-data/).
# Tournament keys rotate; these are the stable per-sport keys as of 2026.
SPORT_KEYS = {
    "tennis": "tennis_atp",
    "basketball": "basketball_nba",
    "baseball": "baseball_mlb",
    "cricket": "cricket_test_match",
    "rugby_union": "rugby_union_international",
    "rugby_league": "rugby_league_nrl",
    "f1": "f1_race_winner",
    "snooker": "snooker",
    "darts": "darts",
}

API_BASE = "https://api.the-odds-api.com/v4"


class NoApiKeyError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.environ.get("ODDS_API_KEY", "").strip()
    if not key:
        raise NoApiKeyError(
            "ODDS_API_KEY is not set. Get a free key at https://the-odds-api.com "
            "and run:  export ODDS_API_KEY=your_key"
        )
    return key


def fetch_the_odds_api(
    sport_key: str,
    out_path: str | Path,
    regions: str = "uk",
    markets: str = "h2h",
    api_key: Optional[str] = None,
) -> Path:
    """Fetch current odds from The Odds API and save raw JSON.

    Returns the path of the saved file. Requires an ODDS_API_KEY (free tier:
    500 requests/month, no credit card).
    """
    key = api_key or _api_key()
    params = urllib.parse.urlencode(
        {"apiKey": key, "regions": regions, "markets": markets, "oddsFormat": "decimal"}
    )
    url = f"{API_BASE}/sports/{sport_key}/odds/?{params}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload: List[Dict[str, Any]] = json.loads(response.read().decode("utf-8"))

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Saved {len(payload)} events from The Odds API ({sport_key}) -> {out}")
    return out


def markets_from_theoddsapi(path: str | Path, sport: str = "") -> List[Market]:
    """Turn a saved The Odds API response into Market objects."""
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    return [Market.from_theoddsapi(event, sport=sport) for event in payload]


def fetch_olbg(sport: str, out_path: str | Path) -> Path:
    """OLBG adapter stub.

    OLBG has no official public API and scraping it may breach its ToS. The
    recommended path is to use The Odds API (fetch-odds --source the-odds-api)
    or to drop a CSV export of odds into data/raw and load it directly.
    """
    raise NotImplementedError(
        "OLBG has no official public API. Options:\n"
        "  1. Use 'python -m olbg_roi fetch-odds --source the-odds-api --sport <key>' "
        "(free key at https://the-odds-api.com).\n"
        "  2. Provide your own odds CSV in the matches/fixtures format documented in "
        "docs/data_sources.md.\n"
        "  3. If you have a legitimate OLBG data licence/export, drop the CSV into "
        "data/raw/ and we can add an importer."
    )


def fetch_odds(source: str, sport: str, out_path: str | Path) -> Path:
    if source == "the-odds-api":
        sport_key = SPORT_KEYS.get(sport)
        if sport_key is None:
            raise ValueError(
                f"no The Odds API key mapping for sport '{sport}' "
                f"(known: {', '.join(sorted(SPORT_KEYS))}); pass --sport-key to override"
            )
        return fetch_the_odds_api(sport_key, out_path)
    if source == "olbg":
        return fetch_olbg(sport, out_path)
    raise ValueError(f"unknown source '{source}' (choose from: olbg, the-odds-api)")
