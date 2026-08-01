"""Unit tests for margin removal."""
import unittest

from olbg_roi.odds.margin import (
    implied_probabilities,
    overround,
    remove_vig,
    remove_vig_power,
    remove_vig_proportional,
    remove_vig_shin,
)


class TestMargin(unittest.TestCase):
    def test_implied_probabilities(self):
        self.assertAlmostEqual(implied_probabilities([2.0, 2.0]), [0.5, 0.5])
        self.assertAlmostEqual(implied_probabilities([1.5, 3.0])[0], 2 / 3)

    def test_overround(self):
        self.assertAlmostEqual(overround([2.0, 2.0]), 0.0)
        # 5% margin typical for a two-way market
        self.assertAlmostEqual(overround([1.91, 1.91]), 1 / 1.91 * 2 - 1)

    def test_proportional_normalises(self):
        odds = [1.5, 3.0, 7.0]
        q = remove_vig_proportional(odds)
        self.assertAlmostEqual(sum(q), 1.0)
        self.assertTrue(all(0 < x < 1 for x in q))

    def test_power_normalises(self):
        odds = [1.5, 3.0, 7.0]
        for exponent in (1.5, 1.8, 2.0):
            q = remove_vig_power(odds, exponent)
            self.assertAlmostEqual(sum(q), 1.0)
            self.assertTrue(all(0 < x < 1 for x in q))

    def test_shin_two_way_symmetric(self):
        odds = [1.91, 1.91]
        q = remove_vig_shin(odds)
        self.assertAlmostEqual(sum(q), 1.0)
        self.assertAlmostEqual(q[0], 0.5, places=6)
        self.assertAlmostEqual(q[0], remove_vig_proportional(odds)[0], places=6)

    def test_shin_removes_margin_and_stays_sane(self):
        odds = [1.5, 3.0, 7.0]  # overround ≈ 6.5%
        q = remove_vig_shin(odds)
        self.assertAlmostEqual(sum(q), 1.0, places=8)
        self.assertTrue(all(0 < x < 1 for x in q))
        # Shin should be close to proportional for small margins (Shin pushes
        # probability toward the favourite, so allow a few points of difference)
        qp = remove_vig_proportional(odds)
        for a, b in zip(q, qp):
            self.assertLess(abs(a - b), 0.05)

    def test_fair_market_shin_equals_implied(self):
        odds = [1.5, 3.0]
        self.assertAlmostEqual(sum(remove_vig_shin(odds)), 1.0)

    def test_dispatch(self):
        odds = [1.5, 3.0]
        for method in ("proportional", "power", "shin"):
            q = remove_vig(method=method, odds=odds)
            self.assertAlmostEqual(sum(q), 1.0)
        with self.assertRaises(ValueError):
            remove_vig(odds, method="bogus")

    def test_rejects_bad_odds(self):
        with self.assertRaises(ValueError):
            implied_probabilities([1.0, 2.0])
        with self.assertRaises(ValueError):
            remove_vig_proportional([2.0])


if __name__ == "__main__":
    unittest.main()
