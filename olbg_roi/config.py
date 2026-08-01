"""Configuration loading.

Config lives in config/config.json at the repo root (or a path given via the
OLBG_CONFIG environment variable). CLI flags override config values.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULTS: Dict[str, Any] = {
    "bankroll": {"initial": 1000.0},
    "betting": {
        "min_edge": 0.03,
        "min_odds": 1.5,
        "min_implied_prob": 0.5,
        "kelly_fraction": 0.25,
        "max_stake_fraction": 0.03,
    },
    "elo": {"start_rating": 1500.0, "k_factor": 32.0, "min_games": 10},
    "paths": {
        "data_dir": "data",
        "models_dir": "models",
        "reports_dir": "reports",
        "predictions_dir": "data/predictions",
    },
}


def _deep_merge(base: Dict, override: Dict) -> Dict:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def repo_root() -> Path:
    """Find the repo root (directory containing config/config.json)."""
    here = Path(__file__).resolve().parent.parent
    if (here / "config" / "config.json").exists():
        return here
    # Fall back to CWD.
    return Path.cwd()


def load_config(path: str | None = None) -> Dict[str, Any]:
    config = json.loads(json.dumps(DEFAULTS))  # deep copy
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    env = os.environ.get("OLBG_CONFIG")
    if env:
        candidates.append(Path(env))
    candidates.extend([repo_root() / "config" / "config.json", Path.cwd() / "config.json"])
    for candidate in candidates:
        if candidate.is_file():
            with open(candidate, encoding="utf-8") as fh:
                config = _deep_merge(config, json.load(fh))
            break
    return config
