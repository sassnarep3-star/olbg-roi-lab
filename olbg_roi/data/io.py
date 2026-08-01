"""CSV / JSON I/O helpers (stdlib only)."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

REQUIRED_MATCH_COLUMNS = {"date", "player_a", "player_b", "score_a"}


def ensure_dir(path: str | Path) -> Path:
    """Ensure `path` exists as a directory and return it."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ensure_parent(path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_matches_csv(path: str | Path) -> List[Dict[str, Any]]:
    """Load historical matches: date, player_a, player_b, score_a (+ optional
    event, odds_a, odds_b, home_a, home_b). score_a in {0, 1} (player_a won)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"matches file not found: {p}")
    rows: List[Dict[str, Any]] = []
    with open(p, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"empty CSV: {p}")
        missing = REQUIRED_MATCH_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{p}: missing required columns {sorted(missing)}; got {reader.fieldnames}"
            )
        for i, raw in enumerate(reader):
            row: Dict[str, Any] = {
                "date": raw["date"].strip(),
                "event": (raw.get("event") or "").strip(),
                "player_a": raw["player_a"].strip(),
                "player_b": raw["player_b"].strip(),
                "score_a": float(raw["score_a"]),
            }
            for col, default in (("odds_a", None), ("odds_b", None)):
                val = (raw.get(col) or "").strip()
                if val:
                    odds = float(val)
                    if odds < 1.01:
                        raise ValueError(f"row {i}: {col}={odds} is not valid decimal odds")
                    row[col] = odds
                else:
                    row[col] = default
            for col in ("home_a", "home_b"):
                val = (raw.get(col) or "").strip().lower()
                row[col] = val in ("1", "true", "yes", "y")
            if row["score_a"] not in (0.0, 1.0, 0.5):
                raise ValueError(f"row {i}: score_a must be 0, 0.5 (draw) or 1; got {row['score_a']}")
            rows.append(row)
    return rows


def load_fixtures_csv(path: str | Path) -> List[Dict[str, Any]]:
    """Load upcoming fixtures: date, player_a, player_b (+ optional event,
    odds_a, odds_b, home_a, home_b)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"fixtures file not found: {p}")
    rows: List[Dict[str, Any]] = []
    with open(p, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"empty CSV: {p}")
        for field in ("date", "player_a", "player_b"):
            if field not in reader.fieldnames:
                raise ValueError(f"{p}: missing required column '{field}'")
        for i, raw in enumerate(reader):
            row: Dict[str, Any] = {
                "date": raw["date"].strip(),
                "event": (raw.get("event") or "").strip(),
                "player_a": raw["player_a"].strip(),
                "player_b": raw["player_b"].strip(),
            }
            for col in ("odds_a", "odds_b"):
                val = (raw.get(col) or "").strip()
                row[col] = float(val) if val else None
            for col in ("home_a", "home_b"):
                val = (raw.get(col) or "").strip().lower()
                row[col] = val in ("1", "true", "yes", "y")
            rows.append(row)
    return rows


def write_csv(path: str | Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> Path:
    p = _ensure_parent(path)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return p


def write_json(path: str | Path, payload: Any) -> Path:
    p = _ensure_parent(path)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return p


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")
