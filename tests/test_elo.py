"""Unit tests for the Elo rating model."""
import json
import tempfile
import unittest
from pathlib import Path

from olbg_roi.ratings.elo import EloModel


class TestElo(unittest.TestCase):
    def test_equal_ratings_even_match(self):
        elo = EloModel()
        self.assertAlmostEqual(elo.win_probability("A", "B"), 0.5)
        self.assertAlmostEqual(elo.expected(1500, 1500), 0.5)

    def test_favourite_beats_underdog(self):
        elo = EloModel()
        self.assertEqual(elo.win_probability("A", "B"), 0.5)  # equal start ratings
        elo.ratings["A"] = 1700.0
        elo.ratings["B"] = 1400.0
        p = elo.win_probability("A", "B")
        self.assertGreater(p, 0.8)
        self.assertAlmostEqual(p + elo.win_probability("B", "A"), 1.0)

    def test_update_moves_ratings(self):
        elo = EloModel()
        elo.update("A", "B", 1.0)  # A beats B
        self.assertGreater(elo.rating("A"), elo.rating("B"))
        self.assertEqual(elo.games_played("A"), 1)
        self.assertEqual(elo.games_played("B"), 1)

    def test_fit_over_1000_matches_converges(self):
        import random
        rng = random.Random(7)
        elo = EloModel(k_factor=40.0)
        matches = []
        for _ in range(1000):
            if rng.random() < 0.7:
                winner, loser = "Strong", "Weak"
            else:
                winner, loser = "Weak", "Strong"
            matches.append({"player_a": winner, "player_b": loser, "score_a": 1.0})
        elo.fit(matches)
        self.assertGreater(elo.rating("Strong"), elo.rating("Weak"))
        # Equilibrium win prob ≈ 0.70 for a 70/30 split
        self.assertGreater(elo.win_probability("Strong", "Weak"), 0.65)

    def test_persistence_roundtrip(self):
        elo = EloModel(k_factor=50.0, home_advantage=30.0)
        elo.update("A", "B", 1.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.json"
            elo.save(path)
            loaded = EloModel.from_json(path)
        self.assertEqual(loaded.k_factor, 50.0)
        self.assertEqual(loaded.home_advantage, 30.0)
        self.assertEqual(loaded.rating("A"), elo.rating("A"))
        self.assertEqual(loaded.games_played("B"), 1)
        self.assertAlmostEqual(
            loaded.win_probability("A", "B"), elo.win_probability("A", "B")
        )

    def test_unknown_player_gets_start_rating(self):
        elo = EloModel()
        self.assertEqual(elo.win_probability("Newbie", "Other"), 0.5)


if __name__ == "__main__":
    unittest.main()
