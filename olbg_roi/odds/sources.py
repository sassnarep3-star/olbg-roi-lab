"""Odds ingestion adapters + caching / rate-limit workarounds.

Multiple sources are supported because the 500-credit/month limit on The
Odds API is too restrictive for long-term research. Alternatives:

- SharpAPI (free tier: 12 req/min, 2 sportsbooks, no card) — REST endpoint
  https://api.sharpapi.io/api/v1/odds
- odds-api.net (free key, OpenAPI-first, mock mode available) — endpoint
  https://api.odds-api.net/v1/sports/{key}/odds
- The Odds API (legacy reference, 500 req/mo)
- Mock / synthetic fallback when no key is available (clear warning printed)

Workarounds implemented here:
1. **Local JSON cache** (`cache/`) — reused for 1 hour by default so 
   repeated CLI calls don't burn credits.
2. **Rate tracker** (`.cache_requests.json` in workspace) — counts 
   requests per source; warns when approaching free-tier limits.
3. **Batch mode** (`batch_fetch`) — fetches for all sports in one call 
   to minimise overhead (still counts per sport, but avoids redundant 
   network overhead).
4. **Mock mode** — if no API key is set, saves synthetic odds with an 
   explicit `"_mock": true` flag. This lets the full pipeline run 
   (`predict`, `backtest`) without burning any credits.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .model import Market

# Optional SDK reference from odds-api repo (cloned / copied into sdk/)
try:
    from .sdk import OddsApiClient, OddsApiError
    SDK_AVAILABLE = True
except Exception:
    SDK_AVAILABLE = False

# ------------------------------------------------------------------ keys
SPORT_KEYS: Dict[str, str] = {
    "tennis": "tennis_atp",
    "basketball": "basketball_nba",
    "baseball": "baseball_mlb",
    "cricket": "cricket_test_match",
    "rugby_union": "rugby_union_international",
    "rugby_league": "rugby_league_nrl",
    "f1": "f1_race_winner",
    "snooker": "snooker",
    "darts": "darts",
    "greyhound": "greyhound_racing",
    "gaelic": "gaelic_football",
}

API_THE_ODDS = "https://api.the-odds-api.com/v4"
API_SHARPAPI = "https://api.sharpapi.io/api/v1"
API_ODDS_API_NET = "https://api.odds-api.net/v1"

# ------------------------------------------------------------------ errors
class NoApiKeyError(RuntimeError):
    pass


class RateLimitWarning(Warning):
    """Raised when we approach the free-tier monthly cap."""


# ------------------------------------------------------------------ helpers

def _env_key(name: str) -> Optional[str]:
    return os.environ.get(name, "").strip() or None


def _request_rate_tracker_path() -> Path:
    # Place tracker inside workspace so it persists across CLI calls.
    p = Path(__file__).resolve().parent.parent.parent / ".cache_requests.json"
    return p


def _load_rate_tracker() -> Dict[str, int]:
    p = _request_rate_tracker_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"the-odds-api": 0, "sharpapi": 0, "odds-api-net": 0}


def _save_rate_tracker(tracker: Dict[str, int]) -> None:
    p = _request_rate_tracker_path()
    try:
        p.write_text(json.dumps(tracker, indent=2), encoding="utf-8")
    except Exception:
        pass


def _increment_rate(source: str) -> None:
    tracker = _load_rate_tracker()
    tracker[source] = tracker.get(source, 0) + 1
    _save_rate_tracker(tracker)
    # Warn thresholds (free-tier approximations)
    limits = {"the-odds-api": 500, "sharpapi": 17280, "odds-api-net": 10000}
    limit = limits.get(source)
    count = tracker[source]
    if limit and count >= limit * 0.9:
        print(f"WARNING: {source} has used {count}/{limit} requests (~{count/limit:.0%}). "
              f"Consider switching sources or enabling cache-only mode.")


# ------------------------------------------------------------------ caching

def _default_cache_dir() -> Path:
    p = Path(__file__).resolve().parent.parent.parent / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cached_path(sport: str, source: str, ext: str = "json") -> Path:
    return _default_cache_dir() / f"{source}_{sport}.{ext}"


def _is_fresh(path: Path, max_age_hours: float = 1.0) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) < max_age_hours * 3600


def _load_cached(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ mock fallback

def _generate_mock_odds(sport_key: str, event_name: str = "Mock Event") -> List[Dict[str, Any]]:
    """Synthetic odds for pipeline testing when no API key is available."""
    # Use a small planted bias similar to the tennis demo so predict works,
    # but clearly tag as synthetic.
    base_odds = [1.65, 2.35]
    mock_events = [
        {
            "sport_key": sport_key,
            "commence_time": "2026-08-01T12:00:00Z",
            "home_team": "Mock A",
            "away_team": "Mock B",
            "bookmakers": [
                {
                    "key": "mock_book",
                    "title": "Mock Bookmaker",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {"name": "Mock A", "price": base_odds[0]},
                                {"name": "Mock B", "price": base_odds[1]},
                            ],
                        }
                    ],
                }
            ],
            "_mock": True,
        }
    ]
    return mock_events


# ------------------------------------------------------------------ adapters

def fetch_the_odds_api(
    sport_key: str,
    out_path: str | Path,
    regions: str = "uk",
    markets: str = "h2h",
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_age_hours: float = 1.0,
) -> Path:
    key = api_key or _env_key("ODDS_API_KEY")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if use_cache and key and _is_fresh(out, max_age_hours):
        print(f"Using cached The Odds API response (<{max_age_hours}h) -> {out}")
        return out

    if not key:
        mock_path = out.with_suffix(".mock.json")
        mock_path.write_text(
            json.dumps(_generate_mock_odds(sport_key), indent=2), encoding="utf-8"
        )
        out.write_text(mock_path.read_text(), encoding="utf-8")
        out.write_text(json.dumps({"_mock": True, "events": _generate_mock_odds(sport_key)}), encoding="utf-8")
        print(
            f"WARNING: No ODDS_API_KEY set. Wrote MOCK odds -> {out} "
            f"(set ODDS_API_KEY for real data). Rate tracker unchanged."
        )
        return out

    params = urllib.parse.urlencode(
        {"apiKey": key, "regions": regions, "markets": markets, "oddsFormat": "decimal"}
    )
    url = f"{API_THE_ODDS}/sports/{sport_key}/odds/?{params}"
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "olbg-roi/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload: List[Dict[str, Any]] = json.loads(response.read().decode("utf-8"))

    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _increment_rate("the-odds-api")
    print(f"Saved {len(payload)} events from The Odds API ({sport_key}) -> {out}")
    return out


def markets_from_theoddsapi(path: str | Path, sport: str = "") -> List[Market]:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict) and payload.get("_mock"):
        payload = payload.get("events", [])
    return [Market.from_theoddsapi(event, sport=sport) for event in payload]


def fetch_sharpapi(
    sport_key: str,
    out_path: str | Path,
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_age_hours: float = 1.0,
) -> Path:
    key = api_key or _env_key("SHARPAPI_KEY")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if use_cache and key and _is_fresh(out, max_age_hours):
        print(f"Using cached SharpAPI response (<{max_age_hours}h) -> {out}")
        return out

    if not key:
        out.write_text(
            json.dumps({"_mock": True, "events": _generate_mock_odds(sport_key)}, indent=2),
            encoding="utf-8",
        )
        print(
            f"WARNING: No SHARPAPI_KEY set. Wrote MOCK odds -> {out} "
            f"(SharpAPI free tier: 12 req/min, 17,280/day, no card at sharpapi.io/sign-up)."
        )
        return out

    # SharpAPI endpoint: /odds accepts sport filter via query param in some docs,
    # but we'll use /events + /odds or direct /odds and filter client-side.
    url = f"{API_SHARPAPI}/odds?sport={sport_key}&markets=h2h"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-API-Key": key,
            "User-Agent": "olbg-roi/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload: Any = json.loads(response.read().decode("utf-8"))

    # SharpAPI returns a dict with an "events" or "data" list; normalise.
    if isinstance(payload, dict):
        events = payload.get("events") or payload.get("data") or payload.get("results") or []
        # Normalise to The-Odds-API-like structure for compatibility.
        normalised: List[Dict[str, Any]] = []
        for ev in events:
            event = {
                "sport_key": sport_key,
                "commence_time": ev.get("start_time") or ev.get("commence_time") or "",
                "home_team": ev.get("home_team") or ev.get("team_1") or ev.get("name_a") or "",
                "away_team": ev.get("away_team") or ev.get("team_2") or ev.get("name_b") or "",
                "bookmakers": [],
            }
            # Try to extract bookmaker odds.
            odds_data = ev.get("odds") or ev.get("market") or ev.get("prices") or {}
            if isinstance(odds_data, list) and odds_data:
                # SharpAPI sometimes returns a flat list of odds per book.
                book_name = ev.get("bookmaker") or "sharp_ref"
                outcomes = []
                for o in odds_data:
                    if isinstance(o, dict) and "price" in o:
                        outcomes.append({"name": o.get("name") or o.get("selection"), "price": float(o["price"])})
                    elif isinstance(o, dict) and "decimal" in o:
                        outcomes.append({"name": o.get("name") or o.get("selection"), "price": float(o["decimal"])})
                if outcomes:
                    event["bookmakers"] = [{"key": book_name, "title": book_name, "markets": [{"key": "h2h", "outcomes": outcomes}]}]
            elif isinstance(odds_data, dict) and "h2h" in odds_data:
                event["bookmakers"] = [
                    {
                        "key": "sharp_ref",
                        "title": "SharpAPI Reference",
                        "markets": [
                            {
                                "key": "h2h",
                                "outcomes": [
                                    {"name": k, "price": float(v)} for k, v in odds_data["h2h"].items()
                                ],
                            }
                        ],
                    }
                ]
            normalised.append(event)
        payload = normalised
    else:
        payload = []

    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _increment_rate("sharpapi")
    count = len(payload) if isinstance(payload, list) else 0
    print(f"Saved {count} events from SharpAPI ({sport_key}) -> {out}")
    return out


def markets_from_sharpapi(path: str | Path, sport: str = "") -> List[Market]:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict) and payload.get("_mock"):
        payload = payload.get("events", [])
    # SharpAPI normalised format is same as The Odds API after adapter.
    return [Market.from_theoddsapi(event, sport=sport) for event in payload if isinstance(event, dict)]


def fetch_odds_api_net(
    sport_key: str,
    out_path: str | Path,
    api_key: Optional[str] = None,
    use_cache: bool = True,
    max_age_hours: float = 1.0,
) -> Path:
    key = api_key or _env_key("ODDS_API_NET_KEY")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if use_cache and key and _is_fresh(out, max_age_hours):
        print(f"Using cached odds-api.net response (<{max_age_hours}h) -> {out}")
        return out

    if not key:
        out.write_text(
            json.dumps({"_mock": True, "events": _generate_mock_odds(sport_key)}, indent=2),
            encoding="utf-8",
        )
        print(
            f"WARNING: No ODDS_API_NET_KEY set. Wrote MOCK odds -> {out} "
            f"(free key at odds-api.net; includes mock mode)."
        )
        return out

    url = f"{API_ODDS_API_NET}/sports/{sport_key}/odds"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-API-Key": key,
            "User-Agent": "olbg-roi/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload: Any = json.loads(response.read().decode("utf-8"))

    # Normalise if needed.
    if isinstance(payload, dict):
        events = payload.get("data") or payload.get("events") or payload.get("results") or []
        payload = events
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _increment_rate("odds-api-net")
    count = len(payload) if isinstance(payload, list) else 0
    print(f"Saved {count} events from odds-api.net ({sport_key}) -> {out}")
    return out


def markets_from_odds_api_net(path: str | Path, sport: str = "") -> List[Market]:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, dict) and payload.get("_mock"):
        payload = payload.get("events", [])
    return [Market.from_theoddsapi(event, sport=sport) for event in payload if isinstance(event, dict)]


# ------------------------------------------------------------------ fetch dispatcher

def fetch_olbg(sport: str, out_path: str | Path) -> Path:
    raise NotImplementedError(
        "OLBG has no official public API. Options:\n"
        "  1. Use 'python -m olbg_roi fetch-odds --source the-odds-api --sport <key>' "
        "(free key at https://the-odds-api.com).\n"
        "  2. Use 'python -m olbg_roi fetch-odds --source sharpapi --sport <key>' "
        "(free key at https://sharpapi.io; 12 req/min, 17,280/day).\n"
        "  3. Use 'python -m olbg_roi fetch-odds --source odds-api-net --sport <key>' "
        "(free key at https://odds-api.net; mock mode available).\n"
        "  4. Provide your own odds CSV in the matches/fixtures format documented in "
        "docs/data_sources.md.\n"
    )


def fetch_odds(
    source: str,
    sport: str,
    out_path: str | Path,
    use_cache: bool = True,
    max_age_hours: float = 1.0,
) -> Path:
    sport_key = SPORT_KEYS.get(sport)
    if sport_key is None:
        raise ValueError(
            f"no key mapping for sport '{sport}' (known: {', '.join(sorted(SPORT_KEYS))}); "
            f"pass --sport-key to override"
        )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if source == "the-odds-api":
        return fetch_the_odds_api(
            sport_key, out_path, api_key=_env_key("ODDS_API_KEY"),
            use_cache=use_cache, max_age_hours=max_age_hours,
        )
    if source == "sharpapi":
        return fetch_sharpapi(
            sport_key, out_path, api_key=_env_key("SHARPAPI_KEY"),
            use_cache=use_cache, max_age_hours=max_age_hours,
        )
    if source == "odds-api-net":
        return fetch_odds_api_net(
            sport_key, out_path, api_key=_env_key("ODDS_API_NET_KEY"),
            use_cache=use_cache, max_age_hours=max_age_hours,
        )
    if source == "olbg":
        return fetch_olbg(sport, out_path)
    raise ValueError(
        f"unknown source '{source}' (choose from: olbg, the-odds-api, sharpapi, odds-api-net)"
    )


# ------------------------------------------------------------------ batch helper

def batch_fetch(
    source: str,
    sports: List[str],
    out_dir: str | Path,
    use_cache: bool = True,
) -> List[Path]:
    """Fetch odds for multiple sports, using cache wherever possible.

    Rate tracker is incremented once per sport (each counts as a request).
    """
    results = []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for sport in sports:
        out = out_dir / f"{sport}_odds_{source}.json"
        results.append(fetch_odds(source, sport, out, use_cache=use_cache))
    return results
