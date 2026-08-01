"""Tests for the demo data generator + end-to-end pipeline sanity."""
import tempfile
import unittest
from pathlib import Path

from olbg_roi.backtest.engine import BacktestConfig, run_backtest
from olbg_roi.data.io import load_fixtures_csv, load_matches_csv
from olbg_roi.demo.generate import generate_tennis_demo
from olbg_roi.odds.margin import overround
from olbg_roi.ratings.elo import EloModel


class TestDemoData(unittest.TestCase):
    def test_generation_and_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = generate_tennis_demo(out_dir=tmp, seed=1, n_seasons=2, matches_per_season=40)
            self.assertEqual(meta["n_seasons"], 2)
            matches = load_matches_csv(Path(tmp) / "tennis_demo.csv")
            self.assertEqual(len(matches), 80)
            fixtures = load_fixtures_csv(Path(tmp) / "tennis_demo_fixtures.csv")
            self.assertGreaterEqual(len(fixtures), 10)
            for m in matches:
                self.assertIn(m["score_a"], (0.0, 1.0))
                self.assertGreater(m["odds_a"], 1.01)
                self.assertGreater(m["odds_b"], 1.01)

    def test_margin_is_planted(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate_tennis_demo(out_dir=tmp, seed=3, n_seasons=1, matches_per_season=30)
            matches = load_matches_csv(Path(tmp) / "tennis_demo.csv")
            margins = [overround([m["odds_a"], m["odds_b"]]) for m in matches]
            avg_margin = sum(margins) / len(margins)
            self.assertGreater(avg_margin, 0.03)
            self.assertLess(avg_margin, 0.08)

    def test_demo_backtest_is_positive(self):
        """The planted bias must surface as positive ROI with the Elo model —
        this validates the whole pipeline (it is NOT evidence of real-world edge)."""
        with tempfile.TemporaryDirectory() as tmp:
            generate_tennis_demo(out_dir=tmp, seed=42, n_seasons=4, matches_per_season=120)
            matches = load_matches_csv(Path(tmp) / "tennis_demo.csv")
            elo = EloModel(k_factor=120.0)  # dynamic K, like the tennis strategy
            config = BacktestConfig(min_games=10)
            result = run_backtest("tennis", matches, elo, config)
            self.assertGreater(result.metrics["bets_placed"], 50)
            self.assertGreater(result.metrics["roi"], 0.0)
            # The market-agreement filter keeps us on favourites
            self.assertLess(result.metrics["avg_odds"], 2.0)


if __name__ == "__main__":
    unittest.main()
