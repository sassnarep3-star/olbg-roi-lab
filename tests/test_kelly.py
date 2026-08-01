"""Unit tests for Kelly staking."""
import unittest

from olbg_roi.betting.kelly import fractional_kelly, kelly_fraction


class TestKelly(unittest.TestCase):
    def test_no_edge_no_stake(self):
        self.assertEqual(kelly_fraction(0.5, 2.0), 0.0)
        self.assertEqual(kelly_fraction(0.4, 2.0), 0.0)

    def test_full_kelly_math(self):
        # p=0.6 at odds 2.0 -> edge 0.2; full kelly = (1.2-1)/1 = 0.2
        self.assertAlmostEqual(kelly_fraction(0.6, 2.0), 0.2)
        # p=0.5 at odds 3.0 -> (1.5-1)/2 = 0.25
        self.assertAlmostEqual(kelly_fraction(0.5, 3.0), 0.25)

    def test_fractional_and_cap(self):
        # full kelly 0.2 -> quarter kelly 0.05; cap at 0.05 -> 0.05
        self.assertAlmostEqual(fractional_kelly(0.6, 2.0, fraction=0.25, max_stake_fraction=0.05), 0.05)
        # cap below kelly
        self.assertAlmostEqual(fractional_kelly(0.6, 2.0, fraction=0.25, max_stake_fraction=0.02), 0.02)
        # no edge -> zero
        self.assertEqual(fractional_kelly(0.5, 2.0), 0.0)

    def test_never_negative(self):
        # p=0.1 at 100.0 is actually +EV (EV = 9.0); use a genuine no-edge case.
        self.assertEqual(kelly_fraction(0.1, 1.5), 0.0)   # EV = -0.85
        self.assertEqual(kelly_fraction(0.6, 1.5), 0.0)   # EV = -0.10
        self.assertEqual(fractional_kelly(0.01, 1.5), 0.0)


if __name__ == "__main__":
    unittest.main()
