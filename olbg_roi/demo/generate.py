"""Synthetic demo data generator.

⚠️ IMPORTANT: this generates *fake* tennis matches with a *planted* bookmaker
bias (favourite–longshot bias) so the full pipeline can be demonstrated end to
end. The positive ROI you see on demo data is manufactured — it proves the
machinery works, not that real tennis has edge.

The generator simulates players with true strengths, matches with logistic
outcomes, and bookmaker odds that systematically misprice longshots. The
planted parameters are written to a sidecar JSON so nobody mistakes this for
real data.
"""
from __future__ import annotations

import json
import math
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

PLAYER_POOL = [
    "A. Novak", "B. Ferreira", "C. Lindqvist", "D. Moreau", "E. Tanaka",
    "F. O'Connell", "G. Petrov", "H. Van Dijk", "I. Costa", "J. Schmidt",
    "K. Mbaye", "L. Kowalski", "M. Rossi", "N. Berg", "O. Silva", "P. Doyle",
    "Q. Nakamura", "R. Ivanov", "S. Okafor", "T. Weber", "U. Karamazov",
    "V. Lindholm", "W. Castillo", "X. Duval", "Y. Haddad", "Z. Novakova",
]


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def generate_tennis_demo(
    out_dir: str | Path = "data/raw",
    seed: int = 42,
    n_seasons: int = 6,
    n_players: int = 16,
    matches_per_season: int = 180,
    bias: float = 0.60,
    margin: float = 0.05,
    form_noise: float = 0.10,
    elo_spread: float = 200.0,
    odds_noise: float = 0.02,
) -> Dict[str, Any]:
    """Generate demo matches + upcoming fixtures + a meta file describing the
    planted bias. Returns the meta dict."""
    rng = random.Random(seed)
    players = PLAYER_POOL[:n_players]
    strengths = {p: rng.gauss(0.0, elo_spread) for p in players}

    def true_logit_p(a: str, b: str) -> float:
        return (strengths[a] - strengths[b]) / 400.0 * math.log(10.0)

    def bookmaker_odds(p_true: float) -> float:
        # Planted favourite–longshot bias + noise + uniform margin.
        # Margin applied by DIVIDING fair odds (bookies offer odds below fair).
        p_book = p_true + bias * (0.5 - p_true) + rng.gauss(0.0, odds_noise)
        p_book = _clamp(p_book, 0.03, 0.97)
        return round((1.0 / p_book) / (1.0 + margin), 2)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    current = date(2019, 1, 7)
    for season in range(n_seasons):
        for i in range(matches_per_season):
            a, b = rng.sample(players, 2)
            p = _sigmoid(true_logit_p(a, b) + rng.gauss(0.0, form_noise))
            score_a = 1.0 if rng.random() < p else 0.0
            p_true = _sigmoid(true_logit_p(a, b))
            rows.append({
                "date": current.isoformat(),
                "event": f"Demo {season + 1}.{i + 1}",
                "player_a": a,
                "player_b": b,
                "score_a": int(score_a),
                "odds_a": bookmaker_odds(p_true),
                "odds_b": bookmaker_odds(1.0 - p_true),
            })
            current += timedelta(days=2)

    matches_path = out / "tennis_demo.csv"
    _write_rows(matches_path, rows)

    # Upcoming fixtures (no result) for the predict step.
    fixtures: List[Dict[str, Any]] = []
    for i in range(12):
        a, b = rng.sample(players, 2)
        p_true = _sigmoid(true_logit_p(a, b))
        fixtures.append({
            "date": (current + timedelta(days=i)).isoformat(),
            "event": f"DemoUpcoming {i + 1}",
            "player_a": a,
            "player_b": b,
            "odds_a": bookmaker_odds(p_true),
            "odds_b": bookmaker_odds(1.0 - p_true),
        })
    fixtures_path = out / "tennis_demo_fixtures.csv"
    _write_rows(fixtures_path, fixtures)

    meta = {
        "dataset": "SYNTHETIC DEMO — do not use for real betting decisions",
        "generator": "olbg_roi.demo.generate.generate_tennis_demo",
        "seed": seed,
        "n_seasons": n_seasons,
        "n_players": n_players,
        "matches_per_season": matches_per_season,
        "planted_bias": {
            "favourite_longshot_bias": bias,
            "uniform_margin": margin,
            "form_noise": form_noise,
            "odds_noise": odds_noise,
            "explanation": (
                "bookmaker implied probabilities are systematically too high for "
                "longshots and too low for favourites; the bias (0.60) is deliberately "
                "exaggerated well beyond anything seen in real markets so the demo "
                "pipeline reliably demonstrates positive ROI. Real markets are far "
                "tighter; finding real edge is the project's actual goal."
            ),
        },
        "files": {
            "matches": str(matches_path),
            "fixtures": str(fixtures_path),
        },
    }
    meta_path = out / "tennis_demo_meta.json"
    with open(meta_path, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    print(f"Demo matches : {len(rows)} rows -> {matches_path}")
    print(f"Fixtures     : {len(fixtures)} rows -> {fixtures_path}")
    print(f"Meta         : {meta_path}  (see planted-bias description)")
    return meta


def _write_rows(path: Path, rows: List[Dict[str, Any]]) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
