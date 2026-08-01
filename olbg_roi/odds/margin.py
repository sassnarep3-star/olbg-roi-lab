"""Bookmaker margin removal (overround stripping).

Bookmaker odds carry a built-in margin (overround), so raw implied
probabilities (1/odds) sum to >1. These methods renormalise them into
estimates of the bookmaker's "true" probabilities.

Methods
-------
proportional : classic 1/odds normalisation (fast, slightly biased towards longshots)
power        : Clarke's power method — p_i^k normalisation, k ≈ 1.8 typical
shin         : Shin (1993) model of insider trading (Štrumbelj 2014 implementation),
               generally the least biased of the three
"""
from __future__ import annotations

import math
from typing import List, Sequence

METHODS = ("proportional", "power", "shin")


def _validate(odds: Sequence[float]) -> None:
    if len(odds) < 2:
        raise ValueError("need at least 2 outcomes to remove margin")
    if any(o < 1.01 for o in odds):
        raise ValueError(f"decimal odds must be >= 1.01: {odds}")


def implied_probabilities(odds: Sequence[float]) -> List[float]:
    _validate(odds)
    return [1.0 / o for o in odds]


def overround(odds: Sequence[float]) -> float:
    """Bookmaker margin as a fraction: sum(1/odds) - 1."""
    return sum(implied_probabilities(odds)) - 1.0


def remove_vig_proportional(odds: Sequence[float]) -> List[float]:
    p = implied_probabilities(odds)
    total = sum(p)
    return [x / total for x in p]


def remove_vig_power(odds: Sequence[float], exponent: float = 1.8) -> List[float]:
    """Power (Clarke) margin removal."""
    p = implied_probabilities(odds)
    total = sum(p)
    weights = [(x / total) ** exponent for x in p]
    weight_sum = sum(weights)
    return [w / weight_sum for w in weights]


def remove_vig_shin(odds: Sequence[float], tol: float = 1e-9) -> List[float]:
    """Shin (1993) margin removal via the Štrumbelj (2014) formulation.

    Solves for z in [0, 1] such that
        sum_i sqrt(z^2 + 4 (1-z) p_i^2 / S) = 2 + z (n - 2)
    then
        q_i = (sqrt(z^2 + 4 (1-z) p_i^2 / S) - z) / (2 (1 - z))
    """
    p = implied_probabilities(odds)
    n = len(p)
    s = sum(p)

    def lhs(z: float) -> float:
        return sum(math.sqrt(z * z + 4.0 * (1.0 - z) * pi * pi / s) for pi in p)

    def f(z: float) -> float:
        return lhs(z) - (2.0 + z * (n - 2.0))

    f0 = f(0.0)
    if abs(f0) <= tol:
        z = 0.0
    elif f0 < 0.0:
        z = 0.0  # arbitrage-style market; use z = 0
    else:
        # f is positive at 0 and f(1) == 0 (trivial root); find the first
        # sign change below 1, then bisect onto it.
        prev_t, found = 0.0, False
        t = 0.0
        while t < 1.0:
            t += 0.02
            if f(t) <= 0.0:
                lo, hi = prev_t, t
                found = True
                break
            prev_t = t
        if not found:
            return remove_vig_proportional(odds)
        while hi - lo > tol:
            mid = 0.5 * (lo + hi)
            if f(mid) > 0.0:
                lo = mid
            else:
                hi = mid
        z = 0.5 * (lo + hi)

    if z >= 1.0 - tol:
        return remove_vig_proportional(odds)

    q = [
        (math.sqrt(z * z + 4.0 * (1.0 - z) * pi * pi / s) - z) / (2.0 * (1.0 - z))
        for pi in p
    ]
    q_sum = sum(q)
    return [x / q_sum for x in q]


def remove_vig(odds: Sequence[float], method: str = "proportional", **kwargs) -> List[float]:
    if method not in METHODS:
        raise ValueError(f"unknown margin method '{method}' (choose from {METHODS})")
    return globals()["remove_vig_" + method](odds, **kwargs)
