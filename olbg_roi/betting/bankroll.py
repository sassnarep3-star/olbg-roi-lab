"""Bankroll accounting: stakes, P&L, ROI."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Bankroll:
    initial: float
    cash: float = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.cash = float(self.initial)
        self.staked_total: float = 0.0
        self.gross_returns: float = 0.0
        self.bets_placed: int = 0
        self.bets_won: int = 0

    @property
    def profit(self) -> float:
        return self.cash - self.initial

    @property
    def roi(self) -> float:
        """Return on total staked."""
        if self.staked_total <= 0:
            return 0.0
        return (self.cash - self.initial) / self.staked_total

    @property
    def strike_rate(self) -> float:
        if self.bets_placed <= 0:
            return 0.0
        return self.bets_won / self.bets_placed

    def settle(self, stake: float, decimal_odds: float, won: bool) -> None:
        self.bets_placed += 1
        self.staked_total += stake
        if won:
            self.bets_won += 1
            returns = stake * decimal_odds
            self.gross_returns += returns
            self.cash += returns - stake
        else:
            self.cash -= stake

    def as_dict(self) -> dict:
        return {
            "initial_bankroll": round(self.initial, 2),
            "final_bankroll": round(self.cash, 2),
            "profit": round(self.profit, 2),
            "total_staked": round(self.staked_total, 2),
            "gross_returns": round(self.gross_returns, 2),
            "bets_placed": self.bets_placed,
            "bets_won": self.bets_won,
            "strike_rate": round(self.strike_rate, 4),
            "roi": round(self.roi, 4),
        }
