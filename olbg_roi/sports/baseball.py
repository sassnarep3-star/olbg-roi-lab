"""Baseball (MLB)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class BaseballStrategy(H2HSportStrategy):
    key = "baseball"
    display_name = "Baseball (MLB)"
    status = "h2h pipeline ready — needs data"
    elo_k = 25.0
    elo_home = 20.0  # MLB home advantage is small but real

    markets = [
        MarketSpec("Moneyline (h2h)", "h2h", "main value market"),
        MarketSpec("Run Line", "handicap", "1.5-run line — handle pushes in backtest"),
        MarketSpec("Totals", "totals", "pitcher-driven"),
        MarketSpec("Pitcher Strikeouts", "player", "M3"),
    ]

    data_sources = [
        DataSourceSpec("MLB Stats API", "https://statsapi.mlb.com", "official, free, no key"),
        DataSourceSpec("Baseball-Reference", "https://www.baseball-reference.com", "advanced stats"),
        DataSourceSpec("Statcast", "https://baseballsavant.mlb.com", "public tracking data"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "baseball_mlb odds"),
    ]

    strategy_notes = (
        "Starting pitcher is ~50% of the moneyline: SP-adjusted team ratings beat plain team "
        "Elo. Bullpen fatigue, day games after night games, park factors and umpire zones "
        "are all public and underweighted. Note the run line can push (dead heat) — the "
        "backtest must handle 0.5-score outcomes and refunded stakes. 162-game season = "
        "big samples; edges are small but countable."
    )
