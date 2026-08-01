"""Pure-Python Elo rating model — the baseline predictive engine.

Elo maps head-to-head results to win probabilities and is a solid baseline for
every h2h sport in this project (tennis, snooker, cricket, rugby, basketball,
darts, baseball, Gaelic). Later milestones will stack richer features on top.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class EloModel:
    start_rating: float = 1500.0
    k_factor: float = 32.0
    home_advantage: float = 0.0  # Elo points added to the home player
    # Dynamic K (FIDE-style): new players move fast, established players settle.
    # Effective K for a player with `g` rated games:
    #   k_min + (k_factor - k_min) * 0.5 ** (g / k_half_life)
    k_min: float = 25.0
    k_half_life: float = 25.0
    ratings: Dict[str, float] = field(default_factory=dict)
    games: Dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------ core
    def expected(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def rating(self, player: str, create: bool = True) -> float:
        if player not in self.ratings and create:
            self.ratings[player] = self.start_rating
            self.games[player] = 0
        return self.ratings.get(player, self.start_rating)

    def k_for(self, player: str) -> float:
        """Effective K factor for a player given their rated-games count."""
        games = self.games.get(player, 0)
        if self.k_factor <= self.k_min:
            return self.k_factor
        return self.k_min + (self.k_factor - self.k_min) * 0.5 ** (games / self.k_half_life)

    def update(
        self,
        player_a: str,
        player_b: str,
        score_a: float,
        home_a: bool = False,
        home_b: bool = False,
    ) -> None:
        """score_a: 1.0 = a won, 0.0 = b won, 0.5 = draw."""
        ra = self.rating(player_a) + (self.home_advantage if home_a else 0.0)
        rb = self.rating(player_b) + (self.home_advantage if home_b else 0.0)
        expected_a = self.expected(ra, rb)
        self.ratings[player_a] = self.rating(player_a) + self.k_for(player_a) * (score_a - expected_a)
        self.ratings[player_b] = self.rating(player_b) + self.k_for(player_b) * (
            (1.0 - score_a) - (1.0 - expected_a)
        )
        self.games[player_a] = self.games.get(player_a, 0) + 1
        self.games[player_b] = self.games.get(player_b, 0) + 1

    def win_probability(
        self, player_a: str, player_b: str, home_a: bool = False, home_b: bool = False
    ) -> float:
        ra = self.rating(player_a, create=False) + (self.home_advantage if home_a else 0.0)
        rb = self.rating(player_b, create=False) + (self.home_advantage if home_b else 0.0)
        return self.expected(ra, rb)

    def games_played(self, player: str) -> int:
        return self.games.get(player, 0)

    def fit(self, results: Iterable[Dict[str, Any]]) -> None:
        """results: iterable of dicts with player_a, player_b, score_a,
        optional home_a/home_b. Order matters — chronological order is best."""
        for row in results:
            self.update(
                row["player_a"],
                row["player_b"],
                float(row["score_a"]),
                bool(row.get("home_a", False)),
                bool(row.get("home_b", False)),
            )

    def player_ratings(self) -> List[Tuple[str, float, int]]:
        return sorted(
            ((p, self.ratings[p], self.games.get(p, 0)) for p in self.ratings),
            key=lambda t: -t[1],
        )

    # ------------------------------------------------------------ persistence
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": "elo",
            "start_rating": self.start_rating,
            "k_factor": self.k_factor,
            "home_advantage": self.home_advantage,
            "k_min": self.k_min,
            "k_half_life": self.k_half_life,
            "ratings": self.ratings,
            "games": self.games,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EloModel":
        return cls(
            start_rating=float(data.get("start_rating", 1500.0)),
            k_factor=float(data.get("k_factor", 32.0)),
            home_advantage=float(data.get("home_advantage", 0.0)),
            k_min=float(data.get("k_min", 25.0)),
            k_half_life=float(data.get("k_half_life", 25.0)),
            ratings={str(k): float(v) for k, v in data.get("ratings", {}).items()},
            games={str(k): int(v) for k, v in data.get("games", {}).items()},
        )

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        return p

    @classmethod
    def from_json(cls, path: str | Path) -> "EloModel":
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"model file not found: {p}")
        with open(p, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
