"""M2 adapter — convert tennis-data.co.uk CSV/Excel to repo match format.

The site (tennis-data.co.uk) provides per-year .xlsx / .csv files with these
columns (from notes.txt):

  Date, Tournament, Surface, Round, Best of, Winner, Loser, WRank, LRank,
  WPts, LPts, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets,
  WinnerOdds (UBL), WinnerOdds (MaxW), WinnerOdds (AvgW),
  LoserOdds (UBL), LoserOdds (MaxL), LoserOdds (AvgL), etc.

This adapter reads the standard format, picks the best-available odds
(AvgW / AvgL preferred; falls back to UBL / Max), and writes:

  date, event, player_a, player_b, score_a, odds_a, odds_b

Score mapping:
  - player_a = Winner → score_a = 1 (win)
  - player_a = Loser → score_a = 0 (loss)

Usage (after downloading a file from tennis-data.co.uk, e.g. 2024.xlsx):

  import openpyxl  # optional; or use csv via pandas export
  # If you have the CSV version:
  python -m olbg_roi.data.tennis_converter \
      --in data/raw/tennis/2024.csv \
      --out data/raw/tennis/2024_repo.csv

Notes:
- The site updates weekly after tournaments. Data dates back to 2000 (ATP)
  and 2007 (WTA).
- Odds columns vary by year; this adapter tries AvgW / AvgL first, then
  UBL / UBL counterpart.
- Always label converted data as real but note that odds are bookmaker
  snapshots, not live feeds.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REQUIRED_IN = {"Date", "Tournament", "Winner", "Loser"}
# Preferred odds columns (in order of preference)
WINNER_ODDS_PREF = [
    "AvgW",
    "MaxW",
    "UBL",
    "WinnerOdds (AvgW)",
    "WinnerOdds (MaxW)",
    "WinnerOdds (UBL)",
]
LOSER_ODDS_PREF = [
    "AvgL",
    "MaxL",
    "UBL",
    "LoserOdds (AvgL)",
    "LoserOdds (MaxL)",
    "LoserOdds (UBL)",
]


def _pick_odds(row: Dict[str, str], pref_list: List[str]) -> Optional[str]:
    for key in pref_list:
        val = row.get(key, "").strip()
        if val:
            try:
                odds = float(val)
                if odds >= 1.01:
                    return val
            except ValueError:
                continue
    return None


def convert_tennis_csv(in_path: str | Path, out_path: Optional[str | Path] = None) -> Path:
    p_in = Path(in_path)
    if not p_in.exists():
        raise FileNotFoundError(f"input file not found: {p_in}")

    out_path = Path(out_path) if out_path else p_in.with_suffix(".repo.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_out: List[Dict[str, Any]] = []
    with open(p_in, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError(f"empty CSV: {p_in}")
        missing = REQUIRED_IN - set(reader.fieldnames)
        if missing:
            # Some files may have slightly different headers; be lenient.
            print(f"NOTE: missing expected columns {sorted(missing)}; available: {reader.fieldnames}")
        for i, raw in enumerate(reader):
            # Map winner as player_a for consistency with positive score_a.
            player_a = (raw.get("Winner") or "").strip()
            player_b = (raw.get("Loser") or "").strip()
            if not player_a or not player_b:
                continue
            event = (raw.get("Tournament") or "").strip()
            date_raw = (raw.get("Date") or "").strip()
            # Some files have date as YYYY-MM-DD; keep as-is.
            score_a = 1.0  # player_a = Winner

            odds_a_raw = _pick_odds(raw, WINNER_ODDS_PREF)
            odds_b_raw = _pick_odds(raw, LOSER_ODDS_PREF)

            row_out = {
                "date": date_raw,
                "event": event,
                "player_a": player_a,
                "player_b": player_b,
                "score_a": score_a,
                "odds_a": float(odds_a_raw) if odds_a_raw else None,
                "odds_b": float(odds_b_raw) if odds_b_raw else None,
            }
            # Add surface/home info if available (optional in repo format)
            surface = (raw.get("Surface") or "").strip()
            if surface:
                row_out["surface"] = surface
            rows_out.append(row_out)

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "date", "event", "player_a", "player_b", "score_a",
            "odds_a", "odds_b", "surface",  # surface optional
        ])
        for r in rows_out:
            writer.writerow([
                r["date"],
                r["event"],
                r["player_a"],
                r["player_b"],
                r["score_a"],
                r.get("odds_a") or "",
                r.get("odds_b") or "",
                r.get("surface", ""),
            ])

    print(f"Converted {len(rows_out)} matches from {p_in} -> {out_path}")
    return out_path


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Convert tennis-data.co.uk CSV to repo format")
    parser.add_argument("--in", dest="in_path", required=True, help="input CSV path")
    parser.add_argument("--out", dest="out_path", help="output CSV path (default: <in>.repo.csv)")
    args = parser.parse_args(argv)
    convert_tennis_csv(args.in_path, args.out_path)


if __name__ == "__main__":
    main()
