"""Walk-forward backtesting engine.

Chronological walk-forward with an *online* model: before each match we
predict with ratings built only from matches that already happened (no
look-ahead bias), bet if there is value, then update the ratings with the
result. This is the honest way to estimate ROI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..betting.bankroll import Bankroll
from ..betting.value import best_value_bet, evaluate_h2h_market
from ..data.io import ensure_dir, timestamp, write_csv, write_json
from ..odds.margin import overround
from ..ratings.elo import EloModel


@dataclass
class BacktestConfig:
    min_edge: float = 0.03
    min_odds: float = 1.5
    min_implied_prob: float = 0.0  # market-agreement filter (e.g. 0.5 = favourites only)
    kelly_fraction: float = 0.25
    max_stake_fraction: float = 0.03
    initial_bankroll: float = 1000.0
    min_games: int = 10       # min rated games per player before we trust a prediction
    start_date: Optional[str] = None  # ISO date; skip matches before it

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestConfig":
        betting = data.get("betting", {})
        bankroll = data.get("bankroll", {})
        elo = data.get("elo", {})
        return cls(
            min_edge=float(betting.get("min_edge", 0.03)),
            min_odds=float(betting.get("min_odds", 1.5)),
            min_implied_prob=float(betting.get("min_implied_prob", 0.0)),
            kelly_fraction=float(betting.get("kelly_fraction", 0.25)),
            max_stake_fraction=float(betting.get("max_stake_fraction", 0.03)),
            initial_bankroll=float(bankroll.get("initial", 1000.0)),
            min_games=int(elo.get("min_games", 10)),
        )


@dataclass
class BacktestResult:
    sport: str
    metrics: Dict[str, Any]
    rows: List[Dict[str, Any]] = field(default_factory=list)   # per-bet rows
    curve: List[float] = field(default_factory=list)           # bankroll over time

    def write(self, out_dir: str | Path, config: BacktestConfig) -> Dict[str, Path]:
        """Write per-bet CSV, summary JSON and a human-readable Markdown report."""
        out = ensure_dir(out_dir)
        stamp = timestamp()
        base = out / f"backtest_{self.sport}_{stamp}"

        fields = [
            "date", "event", "selection", "opponent", "result", "market_odds",
            "model_prob", "implied_prob", "edge", "expected_value", "stake",
            "returns", "bankroll_after",
        ]
        csv_path = write_csv(f"{base}.csv", self.rows, fields)
        json_path = write_json(
            f"{base}.json",
            {
                "sport": self.sport,
                "generated_at": stamp,
                "config": {
                    "min_edge": config.min_edge,
                    "min_odds": config.min_odds,
                    "min_implied_prob": config.min_implied_prob,
                    "kelly_fraction": config.kelly_fraction,
                    "max_stake_fraction": config.max_stake_fraction,
                    "initial_bankroll": config.initial_bankroll,
                    "min_games": config.min_games,
                    "start_date": config.start_date,
                },
                "metrics": self.metrics,
            },
        )
        md_path = write_markdown_report(f"{base}.md", self, config)
        return {"csv": csv_path, "json": json_path, "md": md_path}


def max_drawdown(curve: List[float]) -> float:
    """Largest peak-to-trough drop as a fraction of the peak."""
    peak = curve[0] if curve else 0.0
    worst = 0.0
    for value in curve:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return worst


def run_backtest(
    sport: str,
    matches: List[Dict[str, Any]],
    elo: EloModel,
    config: BacktestConfig,
) -> BacktestResult:
    matches = sorted(matches, key=lambda m: m["date"])
    if config.start_date:
        matches = [m for m in matches if m["date"] >= config.start_date]

    bank = Bankroll(config.initial_bankroll)
    rows: List[Dict[str, Any]] = []
    curve: List[float] = [bank.cash]
    yearly_profit: Dict[str, float] = {}
    total_edge_sum = 0.0
    odds_sum = 0.0

    for match in matches:
        a, b = match["player_a"], match["player_b"]
        score_a = match["score_a"]
        odds_a, odds_b = match.get("odds_a"), match.get("odds_b")
        home_a, home_b = bool(match.get("home_a", False)), bool(match.get("home_b", False))

        if odds_a is not None and odds_b is not None:
            enough_games = (
                elo.games_played(a) >= config.min_games
                and elo.games_played(b) >= config.min_games
            )
            if enough_games:
                p_a = elo.win_probability(a, b, home_a, home_b)
                bets = evaluate_h2h_market(
                    match.get("event") or f"{a} v {b}",
                    a, b, odds_a, odds_b, p_a,
                    min_edge=config.min_edge,
                    min_odds=config.min_odds,
                    min_implied_prob=config.min_implied_prob,
                    kelly_fraction=config.kelly_fraction,
                    max_stake_fraction=config.max_stake_fraction,
                    bankroll=bank.cash,
                )
                bet = best_value_bet(bets)
                if bet is not None and bet.stake > 0 and bet.stake <= bank.cash:
                    won = (score_a == 1.0 and bet.selection == a) or (
                        score_a == 0.0 and bet.selection == b
                    )
                    bank.settle(bet.stake, bet.market_odds, won)
                    returns = bet.stake * bet.market_odds if won else 0.0
                    year = match["date"][:4]
                    yearly_profit[year] = yearly_profit.get(year, 0.0) + (returns - bet.stake)
                    total_edge_sum += bet.edge
                    odds_sum += bet.market_odds
                    rows.append({
                        "date": match["date"],
                        "event": match.get("event") or f"{a} v {b}",
                        "selection": bet.selection,
                        "opponent": b if bet.selection == a else a,
                        "result": "W" if won else "L",
                        "market_odds": round(bet.market_odds, 3),
                        "model_prob": round(bet.model_prob, 4),
                        "implied_prob": round(bet.implied_prob, 4),
                        "edge": round(bet.edge, 4),
                        "expected_value": round(bet.expected_value, 4),
                        "stake": round(bet.stake, 2),
                        "returns": round(returns, 2),
                        "bankroll_after": round(bank.cash, 2),
                    })

        # Update ratings with the result (online / walk-forward, no look-ahead).
        elo.update(a, b, score_a, home_a, home_b)
        curve.append(bank.cash)

    n_bets = len(rows)
    metrics: Dict[str, Any] = {
        "sport": sport,
        "matches_evaluated": len(matches),
        "bets_placed": n_bets,
        "coverage": round(n_bets / len(matches), 4) if matches else 0.0,
        "total_staked": round(bank.staked_total, 2),
        "gross_returns": round(bank.gross_returns, 2),
        "net_profit": round(bank.profit, 2),
        "roi": round(bank.roi, 4),
        "strike_rate": round(bank.strike_rate, 4),
        "avg_odds": round(odds_sum / n_bets, 3) if n_bets else 0.0,
        "avg_edge": round(total_edge_sum / n_bets, 4) if n_bets else 0.0,
        "max_drawdown": round(max_drawdown(curve), 4),
        "final_bankroll": round(bank.cash, 2),
        "profit_by_year": {year: round(p, 2) for year, p in sorted(yearly_profit.items())},
    }
    return BacktestResult(sport=sport, metrics=metrics, rows=rows, curve=curve)


def write_markdown_report(path: str | Path, result: BacktestResult, config: BacktestConfig) -> Path:
    m = result.metrics
    lines = [
        f"# Backtest report — {result.sport}",
        "",
        f"- Generated: {timestamp()}",
        f"- Matches evaluated: {m['matches_evaluated']} | Bets placed: {m['bets_placed']} "
        f"({m['coverage'] * 100:.1f}% coverage)",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Net profit | {m['net_profit']:+.2f} |",
        f"| ROI (on staked) | {m['roi'] * 100:+.2f}% |",
        f"| Strike rate | {m['strike_rate'] * 100:.1f}% |",
        f"| Avg odds | {m['avg_odds']:.3f} |",
        f"| Avg edge | {m['avg_edge'] * 100:+.2f}% |",
        f"| Max drawdown | {m['max_drawdown'] * 100:.1f}% |",
        f"| Final bankroll | {m['final_bankroll']:.2f} |",
        "",
        "## Settings",
        "",
        f"- min_edge: {config.min_edge}, min_odds: {config.min_odds}, "
        f"min_implied_prob: {config.min_implied_prob}, "
        f"kelly_fraction: {config.kelly_fraction}, max_stake_fraction: {config.max_stake_fraction}, "
        f"min_games: {config.min_games}, start_date: {config.start_date}",
        "",
    ]
    years = m.get("profit_by_year") or {}
    if years:
        lines.append("## Profit by year")
        lines.append("")
        lines.append("| Year | Profit |")
        lines.append("|---|---|")
        for year, profit in years.items():
            lines.append(f"| {year} | {profit:+.2f} |")
        lines.append("")
    lines.append("> ⚠️ Synthetic demo data contains a planted bias. Real ROI requires real data "
                 "and rigorous validation — see docs/roadmap.md.")
    return write_csv_path_md(Path(path), "\n".join(lines) + "\n")


def write_csv_path_md(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
