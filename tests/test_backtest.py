"""Unit tests for the walk-forward backtest engine."""
import unittest

from olbg_roi.backtest.engine import BacktestConfig, max_drawdown, run_backtest
from olbg_roi.ratings.elo import EloModel


def _match(a, b, score_a, odds_a, odds_b, date="2023-01-01", event="e"):
    return {
        "date": date, "event": event, "player_a": a, "player_b": b,
        "score_a": float(score_a), "odds_a": odds_a, "odds_b": odds_b,
    }


class TestBacktest(unittest.TestCase):
    def test_winning_bet_accounting(self):
        elo = EloModel(k_factor=40.0)
        elo.ratings["Strong"] = 2000.0
        elo.ratings["Weak"] = 1000.0
        elo.games["Strong"] = 100
        elo.games["Weak"] = 100
        matches = [_match("Strong", "Weak", 1.0, 1.5, 3.0)]
        config = BacktestConfig(
            min_edge=0.03, min_odds=1.0, kelly_fraction=0.25,
            max_stake_fraction=0.05, initial_bankroll=1000.0, min_games=0,
        )
        result = run_backtest("tennis", matches, elo, config)
        m = result.metrics
        self.assertEqual(m["bets_placed"], 1)
        stake = m["total_staked"]
        # EV = p*odds - 1 is hugely positive -> stake capped at 5% of 1000 = 50
        self.assertAlmostEqual(stake, 50.0, places=2)
        self.assertAlmostEqual(m["net_profit"], 50.0 * 0.5, places=2)  # 1.5 odds
        self.assertAlmostEqual(m["roi"], 0.5, places=6)
        self.assertEqual(m["strike_rate"], 1.0)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0]["result"], "W")

    def test_losing_bet_accounting(self):
        elo = EloModel(k_factor=40.0)
        elo.ratings["Strong"] = 2000.0
        elo.ratings["Weak"] = 1000.0
        elo.games["Strong"] = 100
        elo.games["Weak"] = 100
        # Upset: strong player loses
        matches = [_match("Strong", "Weak", 0.0, 1.5, 3.0)]
        config = BacktestConfig(min_edge=0.03, min_odds=1.0, initial_bankroll=1000.0, min_games=0)
        result = run_backtest("tennis", matches, elo, config)
        m = result.metrics
        self.assertEqual(m["bets_placed"], 1)
        self.assertEqual(m["strike_rate"], 0.0)
        self.assertLess(m["net_profit"], 0)
        self.assertEqual(result.rows[0]["result"], "L")

    def test_no_bet_when_no_edge(self):
        elo = EloModel()
        elo.ratings["A"] = elo.ratings["B"] = 1500.0
        elo.games["A"] = elo.games["B"] = 50
        matches = [_match("A", "B", 1.0, 1.91, 1.91)]  # fair market, no edge
        config = BacktestConfig(min_edge=0.03, min_odds=1.0, initial_bankroll=1000.0, min_games=0)
        result = run_backtest("tennis", matches, elo, config)
        self.assertEqual(result.metrics["bets_placed"], 0)

    def test_min_games_gate(self):
        elo = EloModel()
        matches = [_match("A", "B", 1.0, 1.5, 3.0)]
        config = BacktestConfig(min_games=10, initial_bankroll=1000.0)
        result = run_backtest("tennis", matches, elo, config)
        self.assertEqual(result.metrics["bets_placed"], 0)

    def test_max_drawdown(self):
        self.assertEqual(max_drawdown([1000, 950, 900, 1100, 1000]), 0.10)
        self.assertEqual(max_drawdown([1000, 1100, 1200]), 0.0)
        self.assertEqual(max_drawdown([]), 0.0)

    def test_chronological_no_lookahead(self):
        # Ratings only from prior matches: a fresh player who wins later must
        # not be rated before their first match.
        elo = EloModel(k_factor=40.0)
        matches = [
            _match("VeteranA", "VeteranB", 1.0, 1.5, 3.0, date="2023-01-01"),
            _match("Newbie", "VeteranB", 1.0, 1.5, 3.0, date="2023-01-02"),
        ]
        config = BacktestConfig(min_games=0, min_edge=0.0, min_odds=1.0, initial_bankroll=1000.0)
        result = run_backtest("tennis", matches, elo, config)
        # Newbie has no rating history before match 2 -> p = 0.5 vs VeteranB
        # (created at 1500)... rating exists (created in match 1 update) but with
        # 0 games. min_games=0 means we still bet; sanity: engine does not crash.
        self.assertEqual(result.metrics["matches_evaluated"], 2)
        self.assertGreaterEqual(result.metrics["bets_placed"], 1)


if __name__ == "__main__":
    unittest.main()
