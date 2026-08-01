"""Odds layer: market & selection data structures plus loaders."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Selection:
    name: str
    decimal_odds: float

    @property
    def implied_probability(self) -> float:
        return 1.0 / self.decimal_odds


@dataclass
class Market:
    """A single betting market for one event (e.g. match winner for one match)."""
    sport: str
    event: str
    market_type: str = "h2h"
    selections: List[Selection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_selection(self, name: str, decimal_odds: float) -> None:
        if decimal_odds < 1.01:
            raise ValueError(f"invalid decimal odds {decimal_odds} for '{name}'")
        self.selections.append(Selection(name, decimal_odds))

    @classmethod
    def from_h2h_odds(cls, sport: str, event: str, player_a: str, player_b: str,
                      odds_a: float, odds_b: float) -> "Market":
        market = cls(sport=sport, event=event)
        market.add_selection(player_a, odds_a)
        market.add_selection(player_b, odds_b)
        return market

    @classmethod
    def from_theoddsapi(cls, payload: Dict[str, Any], sport: str = "") -> "Market":
        """Build a Market from one The Odds API event payload (h2h market)."""
        event = payload.get("home_team", "") + " vs " + payload.get("away_team", "")
        market = cls(sport=sport or payload.get("sport_key", ""), event=event)
        for outcome in payload.get("bookmakers", []):
            for market_data in outcome.get("markets", []):
                if market_data.get("key") == "h2h":
                    for bet in market_data.get("outcomes", []):
                        market.add_selection(bet["name"], float(bet["price"]))
                    break
            break  # first bookmaker is enough for structure
        return market

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.sport,
            "event": self.event,
            "market_type": self.market_type,
            "selections": [
                {"name": s.name, "decimal_odds": s.decimal_odds, "implied_probability": s.implied_probability}
                for s in self.selections
            ],
        }

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
