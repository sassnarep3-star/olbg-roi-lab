"""Unit tests for value-bet detection."""
import unittest

from olbg_roi.betting.value import best_value_bet, evaluate_h2h_market


class TestValue(unittest.TestCase):
    def test_detects_favourite_value(self):
        # Model says 60%; bookmaker 1.95 (implied ~51.3%) -> positive edge on A
        bets = evaluate_h2h_market(
            "m1", "A", "B", 1.95, 1.95, 0.60,
            min_edge=0.03, min_odds=1.5, bankroll=1000.0,
        )
        by_name = {b.selection: b for b in bets}
        self.assertTrue(by_name["A"].recommended)
        self.assertFalse(by_name["B"].recommended)
        self.assertGreater(by_name["A"].expected_value, 0.15)
        self.assertGreater(by_name["A"].stake, 0)
        self.assertAlmostEqual(by_name["A"].edge, 0.60 - 0.5, places=9)  # 50% implied each

    def test_no_value_no_bet(self):
        bets = evaluate_h2h_market(
            "m1", "A", "B", 1.95, 1.95, 0.52,
            min_edge=0.03, min_odds=1.5, bankroll=1000.0,
        )
        for b in bets:
            self.assertFalse(b.recommended)
        self.assertIsNone(best_value_bet(bets))

    def test_min_odds_filter(self):
        bets = evaluate_h2h_market(
            "m1", "A", "B", 1.40, 3.50, 0.80,
            min_edge=0.03, min_odds=1.5, bankroll=1000.0,
        )
        # A has edge but odds 1.40 < 1.50 -> not recommended
        by_name = {b.selection: b for b in bets}
        self.assertFalse(by_name["A"].recommended)
        self.assertIsNone(best_value_bet(bets))

    def test_best_value_picks_max_edge(self):
        bets = evaluate_h2h_market(
            "m1", "A", "B", 1.95, 1.95, 0.65,
            min_edge=0.03, min_odds=1.5, bankroll=1000.0,
        )
        best = best_value_bet(bets)
        self.assertIsNotNone(best)
        self.assertEqual(best.selection, "A")

    def test_market_agreement_filter(self):
        # Model says 60% but the side is a longshot at 3.0 (implied ~0.33):
        # without the filter -> bet; with min_implied_prob=0.5 -> no bet.
        bets = evaluate_h2h_market(
            "m1", "A", "B", 3.00, 1.50, 0.60,
            min_edge=0.03, min_odds=1.5, min_implied_prob=0.0, bankroll=1000.0,
        )
        self.assertTrue(next(b for b in bets if b.selection == "A").recommended)
        bets = evaluate_h2h_market(
            "m1", "A", "B", 3.00, 1.50, 0.60,
            min_edge=0.03, min_odds=1.5, min_implied_prob=0.5, bankroll=1000.0,
        )
        self.assertFalse(next(b for b in bets if b.selection == "A").recommended)
        self.assertIsNone(best_value_bet(bets))

    def test_stake_scales_with_bankroll(self):
        small = evaluate_h2h_market("m1", "A", "B", 1.95, 1.95, 0.60, bankroll=100.0)
        big = evaluate_h2h_market("m1", "A", "B", 1.95, 1.95, 0.60, bankroll=10000.0)
        a_small = next(b for b in small if b.selection == "A")
        a_big = next(b for b in big if b.selection == "A")
        self.assertAlmostEqual(a_big.stake, a_small.stake * 100.0, places=2)


if __name__ == "__main__":
    unittest.main()
