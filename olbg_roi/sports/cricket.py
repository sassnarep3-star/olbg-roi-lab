"""Cricket (Test / ODI / T20)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class CricketStrategy(H2HSportStrategy):
    key = "cricket"
    display_name = "Cricket (Test / ODI / T20)"
    status = "h2h pipeline ready — needs data"
    elo_k = 30.0

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "per format: Test/ODI/T20"),
        MarketSpec("Top Team Runs", "player", "innings-based (M3)"),
        MarketSpec("Top Batsman / Top Bowler", "player", "soft markets (M3)"),
        MarketSpec("Series Winner", "multi", "multi-match horizon"),
    ]

    data_sources = [
        DataSourceSpec("Cricsheet", "https://cricsheet.org", "ball-by-ball data, CC0 licence"),
        DataSourceSpec("ESPNcricinfo", "https://www.espncricinfo.com", "results, scorecards, rankings"),
        DataSourceSpec("ICC Rankings", "https://www.icc-cricket.com/rankings", "team & player ratings"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "cricket_* odds keys"),
    ]

    strategy_notes = (
        "Never mix formats: fit separate Elo per format (Test/ODI/T20). Tests are 3-way "
        "markets (home/draw/away) — draw probability needs pitch/weather modelling before "
        "h2h edges are trustworthy. T20: toss + dew, powerplay dynamics, and team balance "
        "matter; bookmakers price name recognition over conditions. Home advantage is real "
        "in Tests, weaker in T20 bilaterals. Top-batsman markets are notoriously soft."
    )
