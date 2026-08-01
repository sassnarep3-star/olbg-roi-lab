"""Value-bet detection: model probability vs bookmaker-implied probability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from ..odds.margin import remove_vig_proportional
from .kelly import fractional_kelly


@dataclass
class ValueBet:
    event: str
    selection: str
    model_prob: float
    implied_prob: float
    market_odds: float
    fair_odds: float
    edge: float              # model_prob - implied_prob
    expected_value: float    # model_prob * odds - 1
    stake_fraction: float
    stake: float
    recommended: bool

    def as_dict(self) -> dict:
        return {
            "event": self.event,
            "selection": self.selection,
            "model_prob": round(self.model_prob, 4),
            "implied_prob": round(self.implied_prob, 4),
            "fair_odds": round(self.fair_odds, 3),
            "market_odds": round(self.market_odds, 3),
            "edge": round(self.edge, 4),
            "expected_value": round(self.expected_value, 4),
            "stake_fraction": round(self.stake_fraction, 4),
            "stake": round(self.stake, 2),
            "recommended": self.recommended,
        }


def evaluate_h2h_market(
    event: str,
    player_a: str,
    player_b: str,
    odds_a: float,
    odds_b: float,
    p_a: float,
    *,
    min_edge: float = 0.03,
    min_odds: float = 1.5,
    min_implied_prob: float = 0.0,
    kelly_fraction: float = 0.25,
    max_stake_fraction: float = 0.03,
    bankroll: float = 1000.0,
) -> List[ValueBet]:
    """Evaluate both sides of an h2h market against the model probability.

    Returns one ValueBet per side (typically only one side carries value).

    min_implied_prob > 0 enforces *market agreement*: only bet on a side the
    bookmaker market also favours (e.g. 0.5 = favourites only). This filters
    phantom edges caused by model noise on longshots — the model's edge
    estimate must not contradict the market's direction.
    """
    implied = remove_vig_proportional([odds_a, odds_b])
    model_probs = [p_a, 1.0 - p_a]
    names = [player_a, player_b]
    odds = [odds_a, odds_b]

    bets: List[ValueBet] = []
    for i in range(2):
        fair = 1.0 / model_probs[i] if model_probs[i] > 0 else 999.0
        edge = model_probs[i] - implied[i]
        ev = model_probs[i] * odds[i] - 1.0
        stake_frac = fractional_kelly(model_probs[i], odds[i], kelly_fraction, max_stake_fraction)
        recommended = (
            edge >= min_edge
            and odds[i] >= min_odds
            and implied[i] >= min_implied_prob
            and stake_frac > 0.0
        )
        bets.append(
            ValueBet(
                event=event,
                selection=names[i],
                model_prob=model_probs[i],
                implied_prob=implied[i],
                market_odds=odds[i],
                fair_odds=round(fair, 3),
                edge=edge,
                expected_value=ev,
                stake_fraction=stake_frac,
                stake=round(bankroll * stake_frac, 2) if recommended else 0.0,
                recommended=recommended,
            )
        )
    return bets


def best_value_bet(bets: List[ValueBet]) -> Optional[ValueBet]:
    """Pick the single best recommended bet from a market (max edge)."""
    recommended = [b for b in bets if b.recommended]
    if not recommended:
        return None
    return max(recommended, key=lambda b: b.edge)
