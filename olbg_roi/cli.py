"""Command-line interface for olbg-roi-lab.

Commands
--------
list-sports   Show all registered sports, markets and data sources
init-demo     Generate the synthetic tennis demo dataset
fetch-odds    Pull bookmaker odds (The Odds API / OLBG guidance)
fit           Train (fit) a sport's baseline model on match history
backtest      Walk-forward ROI backtest of a sport's strategy
predict       Generate predictions & value bets for upcoming fixtures
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__
from .config import load_config


def _sport_choice() -> str:
    from .sports import all_sport_keys
    return ", ".join(all_sport_keys())


# ---------------------------------------------------------------------- utils
def _fmt(x: Any, width: int = 10) -> str:
    if x is None:
        return "-".rjust(width)
    if isinstance(x, float):
        return f"{x:,.3f}".rjust(width)
    if isinstance(x, int):
        return f"{x:,}".rjust(width)
    return str(x).rjust(width)


def _print_predictions_table(rows: List[Dict[str, Any]]) -> None:
    print("\nPredictions (recommended bets first):")
    header = ("DATE", "EVENT", "SELECTION", "P_MODEL", "FAIR", "BOOK", "EDGE", "EV", "STAKE", "BET?")
    print("  " + " | ".join(h.center(12) for h in header))
    print("  " + "-" * 118)
    for row in rows:
        rec = "YES" if row.get("recommended") else "no"
        note = row.get("note") or ""
        print("  " + " | ".join([
            str(row["date"])[:10].center(12),
            (row["event"] or "")[:12].center(12),
            (row["selection"] or "")[:12].center(12),
            _fmt(row.get("model_prob")).center(12),
            _fmt(row.get("fair_odds")).center(12),
            _fmt(row.get("market_odds")).center(12),
            _fmt(row.get("edge")).center(12),
            _fmt(row.get("expected_value")).center(12),
            _fmt(row.get("stake")).center(12),
            rec.center(12),
        ]) + ("  " + note if note else ""))
    print()


def _print_backtest_summary(result, files: Dict[str, Path]) -> None:
    m = result.metrics
    print(f"\nBacktest — {m['sport']}: {m['matches_evaluated']} matches evaluated, "
          f"{m['bets_placed']} bets placed ({m['coverage'] * 100:.1f}% coverage)")
    print(f"  staked      : {m['total_staked']:>12,.2f}")
    print(f"  net profit  : {m['net_profit']:>+12,.2f}")
    print(f"  ROI         : {m['roi'] * 100:>+11.2f}%")
    print(f"  strike rate : {m['strike_rate'] * 100:>10.1f}%")
    print(f"  avg odds    : {m['avg_odds']:>12.3f}")
    print(f"  avg edge    : {m['avg_edge'] * 100:>+11.2f}%")
    print(f"  max drawdown: {m['max_drawdown'] * 100:>10.1f}%")
    print(f"  final bank  : {m['final_bankroll']:>12,.2f}")
    if m.get("profit_by_year"):
        print("  by year     : " + ", ".join(f"{y}: {p:+.0f}" for y, p in m["profit_by_year"].items()))
    print(f"\nReports: {files['md']}")
    print(f"          {files['csv']}")
    print(f"          {files['json']}\n")


# ------------------------------------------------------------ sub-commands
def cmd_list_sports(args: argparse.Namespace) -> None:
    from .sports import all_sports, get_sport
    if args.sport:
        sports = [get_sport(args.sport)]
    else:
        sports = all_sports()
    for sport in sports:
        info = sport.describe()
        print(f"\n[{info['key']}] {info['display_name']}  —  {info['status']}  "
              f"({info['outcome_type']})")
        if info["markets"]:
            print("  markets:")
            for m in info["markets"]:
                print(f"    - {m['name']:<42} [{m['kind']}] {m['notes']}")
        if info["data_sources"]:
            print("  public data sources:")
            for s in info["data_sources"]:
                print(f"    - {s['name']:<42} {s['url']}  ({s['notes']})")
        print("  strategy notes:")
        for line in info["strategy_notes"].split(". "):
            if line.strip():
                print(f"    · {line.strip()}")


def cmd_init_demo(args: argparse.Namespace) -> None:
    from .demo.generate import generate_tennis_demo
    generate_tennis_demo(out_dir=args.out, seed=args.seed)


def cmd_fetch_odds(args: argparse.Namespace) -> None:
    from .odds.sources import fetch_odds
    out = Path(args.out) / f"{args.sport}_odds.json"
    try:
        path = fetch_odds(args.source, args.sport, out)
        print(f"Saved odds -> {path}")
        print("Tip: convert to a fixtures CSV (date,event,player_a,player_b,odds_a,odds_b) "
              "for use with 'predict'.")
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"Fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)


def _get_sport_or_exit(sport_key: str):
    from .sports import get_sport
    try:
        return get_sport(sport_key)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


def cmd_fit(args: argparse.Namespace) -> None:
    sport = _get_sport_or_exit(args.sport)
    try:
        path = sport.fit(args.data, args.out, load_config(args.config))
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"Model saved -> {path}")


def cmd_backtest(args: argparse.Namespace) -> None:
    sport = _get_sport_or_exit(args.sport)
    try:
        result, files = sport.backtest(args.data, load_config(args.config), args.out, args.start)
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    _print_backtest_summary(result, files)


def cmd_predict(args: argparse.Namespace) -> None:
    sport = _get_sport_or_exit(args.sport)
    try:
        csv_path, json_path = sport.predict(
            args.fixtures, args.model, args.odds, args.bankroll, args.out, load_config(args.config)
        )
    except NotImplementedError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"\nPredictions written -> {csv_path}")
    print(f"                        {json_path}")
    # Pretty-print the recommendations.
    import json as _json
    with open(json_path, encoding="utf-8") as fh:
        payload = _json.load(fh)
    _print_predictions_table(payload["predictions"])
    recs = [p for p in payload["predictions"] if p.get("recommended")]
    if recs:
        print(f"{len(recs)} recommended bet(s) — always validate odds at the bookmaker "
              "before staking (lines move).\n")


# ----------------------------------------------------------------------- CLI
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="olbg-roi",
        description="OLBG ROI Lab — positive-ROI betting strategy research.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    p = sub.add_parser("list-sports", help="show registered sports, markets and sources")
    p.add_argument("--sport", help="filter by sport key")
    p.set_defaults(func=cmd_list_sports)

    p = sub.add_parser("init-demo", help="generate synthetic demo data (tennis)")
    p.add_argument("--out", default="data/raw", help="output directory (default: data/raw)")
    p.add_argument("--seed", type=int, default=42)
    p.set_defaults(func=cmd_init_demo)

    p = sub.add_parser("fetch-odds", help="pull current bookmaker odds")
    p.add_argument("--source", choices=["olbg", "the-odds-api"], default="the-odds-api")
    p.add_argument("--sport", required=True, help=f"sport key ({_sport_choice()})")
    p.add_argument("--out", default="data/raw")
    p.set_defaults(func=cmd_fetch_odds)

    p = sub.add_parser("fit", help="train the baseline model on match history")
    p.add_argument("--sport", required=True, help=f"sport key ({_sport_choice()})")
    p.add_argument("--data", required=True, help="matches CSV (date,player_a,player_b,score_a[,odds_a,odds_b])")
    p.add_argument("--out", default="models", help="model output dir (default: models)")
    p.add_argument("--config", help="path to a config JSON (default: config/config.json)")
    p.set_defaults(func=cmd_fit)

    p = sub.add_parser("backtest", help="walk-forward ROI backtest")
    p.add_argument("--sport", required=True, help=f"sport key ({_sport_choice()})")
    p.add_argument("--data", required=True, help="historical matches CSV")
    p.add_argument("--out", default="reports", help="report output dir (default: reports)")
    p.add_argument("--start", help="only backtest matches from this ISO date onwards")
    p.add_argument("--config", help="path to a config JSON (default: config/config.json)")
    p.set_defaults(func=cmd_backtest)

    p = sub.add_parser("predict", help="generate predictions & value bets for fixtures")
    p.add_argument("--sport", required=True, help=f"sport key ({_sport_choice()})")
    p.add_argument("--fixtures", required=True, help="fixtures CSV (date,player_a,player_b[,odds_a,odds_b])")
    p.add_argument("--model", required=True, help="trained model JSON (e.g. models/elo_tennis.json)")
    p.add_argument("--odds", help="optional sidecar odds CSV")
    p.add_argument("--bankroll", type=float, default=1000.0, help="current bankroll for staking")
    p.add_argument("--out", default="data/predictions")
    p.add_argument("--config", help="path to a config JSON (default: config/config.json)")
    p.set_defaults(func=cmd_predict)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
