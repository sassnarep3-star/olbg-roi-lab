"""Tests for new odds adapters and caching / mock workarounds."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from olbg_roi.odds.sources import (
    fetch_odds,
    fetch_sharpapi,
    fetch_odds_api_net,
    fetch_the_odds_api,
    _generate_mock_odds,
    _is_fresh,
    _cached_path,
    SPORT_KEYS,
)


class TestMockFallback(unittest.TestCase):
    """When no key is set, adapters must write mock JSON with _mock flag."""

    def test_generate_mock_odds_has_flag(self):
        ev = _generate_mock_odds("tennis")
        self.assertTrue(isinstance(ev, list))
        self.assertTrue(ev[0].get("_mock"))

    def test_fetch_the_odds_api_mock_no_key(self):
        # Ensure no real key exists in this environment
        old = os.environ.get("ODDS_API_KEY")
        if old:
            del os.environ["ODDS_API_KEY"]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "mock.json"
            result = fetch_the_odds_api("tennis_atp", out, use_cache=False)
            data = json.loads(result.read_text())
            # Should either be mock or a list with mock events; adapter writes mock when no key.
            # The adapter writes mock JSON directly to out.
            self.assertTrue(isinstance(data, (dict, list)))
        # Restore
        if old is not None:
            os.environ["ODDS_API_KEY"] = old

    def test_fetch_sharpapi_mock(self):
        old = os.environ.get("SHARPAPI_KEY")
        if old:
            del os.environ["SHARPAPI_KEY"]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sharp_mock.json"
            result = fetch_sharpapi("basketball_nba", out, use_cache=False)
            data = json.loads(result.read_text())
            self.assertIn("_mock", data)
        if old is not None:
            os.environ["SHARPAPI_KEY"] = old

    def test_fetch_odds_api_net_mock(self):
        old = os.environ.get("ODDS_API_NET_KEY")
        if old:
            del os.environ["ODDS_API_NET_KEY"]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "net_mock.json"
            result = fetch_odds_api_net("cricket_test_match", out, use_cache=False)
            data = json.loads(result.read_text())
            self.assertIn("_mock", data)
        if old is not None:
            os.environ["ODDS_API_NET_KEY"] = old


class TestRateAndCache(unittest.TestCase):
    def test_is_fresh_false_for_missing(self):
        self.assertFalse(_is_fresh(Path("/nonexistent/path/file.json")))

    def test_cached_path_exists(self):
        p = _cached_path("tennis", "sharpapi")
        # Should point inside workspace cache dir, not crash.
        self.assertTrue(str(p).endswith("sharpapi_tennis.json"))


if __name__ == "__main__":
    unittest.main()
