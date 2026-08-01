"""Sport strategy framework: registry, metadata, and the h2h baseline pipeline."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from ..ratings.elo import EloModel


@dataclass
class MarketSpec:
    name: str
    kind: str = "h2h"          # h2h | handicap | totals | player | multi | exotic
    notes: str = ""


@dataclass
class DataSourceSpec:
    name: str
    url: str
    notes: str = ""


class SportStrategy(ABC):
    """One strategy per sport. `outcome_type` drives the pipeline:
    - 'h2h'  → Elo baseline (fit / backtest / predict all implemented)
    - 'multi'→ multi-outcome markets (F1 race winner, greyhound); planned M6
    """

    key: str = ""
    display_name: str = ""
    outcome_type: str = "h2h"
    markets: List[MarketSpec] = field(default_factory=list)
    data_sources: List[DataSourceSpec] = field(default_factory=list)
    strategy_notes: str = ""
    status: str = "planned"

    # Elo tuning (overridable per sport)
    elo_k: float = 32.0
    elo_k_min: float = 25.0
    elo_k_half_life: float = 25.0
    elo_home: float = 0.0

    # ------------------------------------------------------------- metadata
    def describe(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "display_name": self.display_name,
            "outcome_type": self.outcome_type,
            "status": self.status,
            "markets": [m.__dict__ for m in self.markets],
            "data_sources": [s.__dict__ for s in self.data_sources],
            "strategy_notes": self.strategy_notes,
        }

    # ------------------------------------------------------------- pipeline
    def _new_elo(self, config: Optional[Dict[str, Any]] = None) -> EloModel:
        elo_cfg = (config or {}).get("elo", {})
        return EloModel(
            start_rating=float(elo_cfg.get("start_rating", 1500.0)),
            k_factor=self.elo_k,
            k_min=float(elo_cfg.get("k_min", self.elo_k_min)),
            k_half_life=float(elo_cfg.get("k_half_life", self.elo_k_half_life)),
            home_advantage=self.elo_home,
        )

    @abstractmethod
    def fit(self, matches_csv: str | Path, model_out: str | Path,
            config: Optional[Dict[str, Any]] = None) -> Path:
        ...

    @abstractmethod
    def backtest(self, matches_csv: str | Path, config: Optional[Dict[str, Any]] = None,
                 out_dir: str | Path = "reports", start_date: Optional[str] = None):
        ...

    @abstractmethod
    def predict(self, fixtures_csv: str | Path, model_path: str | Path,
                odds_csv: Optional[str | Path] = None, bankroll: float = 1000.0,
                out_dir: str | Path = "data/predictions",
                config: Optional[Dict[str, Any]] = None) -> Tuple[Path, Path]:
        ...


class H2HSportStrategy(SportStrategy):
    """Baseline h2h pipeline: Elo ratings fit on match history, walk-forward
    backtest, and fixture predictions. Works for every h2h sport in the repo —
    each sport only needs to set its metadata and Elo tuning."""

    outcome_type = "h2h"

    def _matches_csv(self, matches_csv: str | Path) -> str | Path:
        return matches_csv

    def fit(self, matches_csv: str | Path, model_out: str | Path,
            config: Optional[Dict[str, Any]] = None) -> Path:
        from ..data.io import load_matches_csv
        matches = load_matches_csv(matches_csv)
        elo = self._new_elo(config)
        elo.fit(matches)
        path = Path(model_out) / f"elo_{self.key}.json"
        elo.save(path)
        print(f"Fitted Elo model: {len(elo.ratings)} players, "
              f"{sum(elo.games.values()) // 2} matches -> {path}")
        return path

    def backtest(self, matches_csv: str | Path, config: Optional[Dict[str, Any]] = None,
                 out_dir: str | Path = "reports", start_date: Optional[str] = None):
        from ..backtest.engine import BacktestConfig, run_backtest
        from ..data.io import load_matches_csv

        cfg = BacktestConfig.from_dict(config or {})
        cfg.start_date = start_date
        matches = load_matches_csv(matches_csv)
        elo = self._new_elo(config)
        result = run_backtest(self.key, matches, elo, cfg)
        files = result.write(out_dir, cfg)
        return result, files

    def predict(self, fixtures_csv: str | Path, model_path: str | Path,
                odds_csv: Optional[str | Path] = None, bankroll: float = 1000.0,
                out_dir: str | Path = "data/predictions",
                config: Optional[Dict[str, Any]] = None) -> Tuple[Path, Path]:
        from ..predict.pipeline import run_predictions
        betting = (config or {}).get("betting", {})
        return run_predictions(
            self.key,
            fixtures_csv,
            model_path,
            odds_csv,
            bankroll=bankroll,
            out_dir=out_dir,
            min_edge=float(betting.get("min_edge", 0.03)),
            min_odds=float(betting.get("min_odds", 1.5)),
            min_implied_prob=float(betting.get("min_implied_prob", 0.0)),
            kelly_fraction=float(betting.get("kelly_fraction", 0.25)),
            max_stake_fraction=float(betting.get("max_stake_fraction", 0.03)),
        )


class MultiOutcomeSportStrategy(SportStrategy):
    """Placeholder for multi-outcome sports (F1, greyhound)."""

    outcome_type = "multi"

    def _not_implemented(self) -> None:
        raise NotImplementedError(
            f"'{self.key}' is a multi-outcome sport ({self.outcome_type}); the "
            "softmax-over-ratings pipeline lands in milestone M6 — see "
            "docs/roadmap.md. Meanwhile you can still use the h2h pipeline on "
            "pairwise markets (e.g. driver h2h) once we ship it."
        )

    def fit(self, *args, **kwargs) -> Path:
        self._not_implemented()

    def backtest(self, *args, **kwargs):
        self._not_implemented()

    def predict(self, *args, **kwargs) -> Tuple[Path, Path]:
        self._not_implemented()


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
_REGISTRY: Dict[str, Type[SportStrategy]] = {}


def register(cls: Type[SportStrategy]) -> Type[SportStrategy]:
    if not cls.key:
        raise ValueError(f"{cls.__name__} must define a key")
    _REGISTRY[cls.key] = cls
    return cls


def get_sport(key: str) -> SportStrategy:
    if key not in _REGISTRY:
        raise KeyError(
            f"unknown sport '{key}'. Available: {', '.join(all_sport_keys())}"
        )
    return _REGISTRY[key]()


def all_sport_keys() -> List[str]:
    return sorted(_REGISTRY)


def all_sports() -> List[SportStrategy]:
    return [get_sport(k) for k in all_sport_keys()]
