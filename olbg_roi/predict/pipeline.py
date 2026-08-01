"""Prediction pipeline: fixtures + trained model + bookmaker odds → value bets.

This is the "generate predictions from the model" entry point — the output is
a ranked list of recommended bets with probability, fair odds, edge, expected
value and the suggested Kelly stake.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..betting.value import ValueBet, evaluate_h2h_market
from ..data.io import ensure_dir, load_fixtures_csv, timestamp, write_csv, write_json
from ..ratings.elo import EloModel


def _model_prob(elo: EloModel, fixture: Dict[str, Any]) -> float:
    return elo.win_probability(
        fixture["player_a"],
        fixture["player_b"],
        bool(fixture.get("home_a", False)),
        bool(fixture.get("home_b", False)),
    )


def run_predictions(
    sport: str,
    fixtures_path: str | Path,
    model_path: str | Path,
    odds_path: Optional[str | Path] = None,
    bankroll: float = 1000.0,
    out_dir: str | Path = "data/predictions",
    min_edge: float = 0.03,
    min_odds: float = 1.5,
    min_implied_prob: float = 0.0,
    kelly_fraction: float = 0.25,
    max_stake_fraction: float = 0.03,
) -> Tuple[Path, Path]:
    """Predict upcoming fixtures. Returns (csv_path, json_path)."""
    elo = EloModel.from_json(model_path)
    fixtures = load_fixtures_csv(fixtures_path)

    # Optional sidecar odds file: event -> (odds_a, odds_b)
    odds_map: Dict[str, Tuple[float, float]] = {}
    if odds_path:
        for row in load_fixtures_csv(odds_path):
            if row.get("odds_a") and row.get("odds_b"):
                key = row.get("event") or f"{row['player_a']} v {row['player_b']}"
                odds_map[key] = (float(row["odds_a"]), float(row["odds_b"]))

    predictions: List[Dict[str, Any]] = []
    for fixture in fixtures:
        event = fixture.get("event") or f"{fixture['player_a']} v {fixture['player_b']}"
        p_a = _model_prob(elo, fixture)
        odds_a = fixture.get("odds_a")
        odds_b = fixture.get("odds_b")
        if odds_a is None or odds_b is None:
            key = event
            if key in odds_map:
                odds_a, odds_b = odds_map[key]

        if odds_a and odds_b:
            bets = evaluate_h2h_market(
                event,
                fixture["player_a"],
                fixture["player_b"],
                float(odds_a),
                float(odds_b),
                p_a,
                min_edge=min_edge,
                min_odds=min_odds,
                min_implied_prob=min_implied_prob,
                kelly_fraction=kelly_fraction,
                max_stake_fraction=max_stake_fraction,
                bankroll=bankroll,
            )
            for bet in bets:
                row = {
                    "date": fixture["date"],
                    "event": event,
                    "player_a": fixture["player_a"],
                    "player_b": fixture["player_b"],
                    **bet.as_dict(),
                }
                predictions.append(row)
        else:
            predictions.append({
                "date": fixture["date"],
                "event": event,
                "player_a": fixture["player_a"],
                "player_b": fixture["player_b"],
                "selection": fixture["player_a"],
                "model_prob": round(p_a, 4),
                "fair_odds": round(1.0 / p_a, 3),
                "market_odds": None,
                "implied_prob": None,
                "edge": None,
                "expected_value": None,
                "stake_fraction": 0.0,
                "stake": 0.0,
                "recommended": False,
                "note": "no bookmaker odds — model fair odds only",
            })

    recommended = [p for p in predictions if p.get("recommended")]
    recommended.sort(key=lambda p: -p["expected_value"])

    out = ensure_dir(out_dir)
    stamp = timestamp()
    fields = [
        "date", "event", "player_a", "player_b", "selection", "model_prob",
        "implied_prob", "fair_odds", "market_odds", "edge", "expected_value",
        "stake_fraction", "stake", "recommended", "note",
    ]
    csv_path = write_csv(out / f"predictions_{sport}_{stamp}.csv", predictions, fields)
    json_path = write_json(
        out / f"predictions_{sport}_{stamp}.json",
        {
            "sport": sport,
            "generated_at": stamp,
            "model": str(model_path),
            "bankroll": bankroll,
            "settings": {
                "min_edge": min_edge,
                "min_odds": min_odds,
                "min_implied_prob": min_implied_prob,
                "kelly_fraction": kelly_fraction,
                "max_stake_fraction": max_stake_fraction,
            },
            "summary": {
                "fixtures": len(fixtures),
                "recommended_bets": len(recommended),
            },
            "predictions": predictions,
        },
    )
    return csv_path, json_path
