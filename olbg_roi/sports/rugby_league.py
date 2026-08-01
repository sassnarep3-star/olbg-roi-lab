"""Rugby league (NRL / Super League)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class RugbyLeagueStrategy(H2HSportStrategy):
    key = "rugby_league"
    display_name = "Rugby League (NRL / Super League)"
    status = "h2h pipeline ready — needs data"
    elo_k = 34.0
    elo_home = 40.0

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "NRL + Super League"),
        MarketSpec("Handicap", "handicap", "line betting"),
        MarketSpec("Totals (points)", "totals", "weather-sensitive in winter codes"),
        MarketSpec("First Try Scorer", "exotic", "very soft market (M3)"),
    ]

    data_sources = [
        DataSourceSpec("NRL.com", "https://www.nrl.com", "official results & stats"),
        DataSourceSpec("Super League", "https://www.superleague.co.uk", "official results & stats"),
        DataSourceSpec("Rugby League Project", "https://www.rugbyleagueproject.org", "historic results archive"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "rugby_league_nrl odds"),
    ]

    strategy_notes = (
        "NRL specifics: 5-day turnarounds and long-haul travel (e.g. Perth/Brisbane trips) "
        "are real fatigue signals; ladder position is over-weighted by the market vs actual "
        "form. Winter wet weather drags totals down — price weather explicitly. Super League "
        "is lower-scoring and less liquid; smaller limits but softer lines. Start with "
        "match winner, add handicaps after 1k+ sample."
    )
