"""Staking rules: fractional Kelly with caps."""
from __future__ import annotations


def kelly_fraction(p: float, decimal_odds: float) -> float:
    """Full Kelly fraction: (p*odds - 1) / (odds - 1). 0 when no edge."""
    b = decimal_odds - 1.0
    if b <= 0.0:
        return 0.0
    f = (p * decimal_odds - 1.0) / b
    return max(f, 0.0)


def fractional_kelly(
    p: float,
    decimal_odds: float,
    fraction: float = 0.25,
    max_stake_fraction: float = 0.03,
) -> float:
    """Fraction of bankroll to stake.

    Full Kelly maximises long-run growth but is dangerously volatile; we use a
    fraction of it (default 1/4) and hard-cap the stake (default 3% of bankroll)
    so a cold streak never wipes the bankroll.
    """
    f = kelly_fraction(p, decimal_odds) * fraction
    return min(max(f, 0.0), max_stake_fraction)
