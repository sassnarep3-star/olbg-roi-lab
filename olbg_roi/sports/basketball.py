"""Basketball (NBA / EuroLeague)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class BasketballStrategy(H2HSportStrategy):
    key = "basketball"
    display_name = "Basketball (NBA / EuroLeague)"
    status = "h2h pipeline ready — needs data"
    elo_k = 30.0
    elo_home = 65.0  # NBA home advantage ≈ 2.5–3.5 points

    markets = [
        MarketSpec("Moneyline (h2h)", "h2h", "NBA + EuroLeague"),
        MarketSpec("Spread", "handicap", "point spread"),
        MarketSpec("Totals", "totals", "pace-driven"),
        MarketSpec("1st Half / Quarter lines", "exotic", "M3"),
    ]

    data_sources = [
        DataSourceSpec("NBA Stats API", "https://stats.nba.com", "public stats endpoints"),
        DataSourceSpec("balldontlie", "https://balldontlie.io", "free NBA API (no key)"),
        DataSourceSpec("Basketball-Reference", "https://www.basketball-reference.com", "advanced stats"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "basketball_nba, basketball_euroleague"),
    ]

    strategy_notes = (
        "Schedule is the edge: back-to-backs, rest days and travel are mechanical, "
        "quantifiable signals the market prices slowly. Totals track pace & possessions — "
        "model pace, then totals fall out. Injury reports (star sit-outs) create sharp "
        "intraday moves; our edge is pre-empting them with load-management models. "
        "EuroLeague: smaller sample, travel across time zones, stronger home court."
    )
