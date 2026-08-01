"""Rugby union."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class RugbyUnionStrategy(H2HSportStrategy):
    key = "rugby_union"
    display_name = "Rugby Union"
    status = "h2h pipeline ready — needs data"
    elo_k = 32.0
    elo_home = 55.0  # home advantage ≈ 2–3 points in handicap terms

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "internationals + club (URC/Top14/Premiership)"),
        MarketSpec("Handicap", "handicap", "points handicap"),
        MarketSpec("Totals (points)", "totals", "weather-sensitive"),
        MarketSpec("Winning Margin", "exotic", "M3"),
    ]

    data_sources = [
        DataSourceSpec("ESPN Scrum", "https://www.espn.co.uk/rugby", "results & fixtures archive"),
        DataSourceSpec("RugbyPass", "https://www.rugbypass.com", "results, stats, news"),
        DataSourceSpec("World Rugby Rankings", "https://www.world.rugby/rankings", "official team ratings"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "rugby_union_* odds keys"),
    ]

    strategy_notes = (
        "Home advantage is worth roughly 2–4 points in handicap terms — price it explicitly. "
        "Tier gaps (T1 vs T2 nations) create structural mispricing in internationals. "
        "Club competitions: travel across leagues (EPCR) and rotation ahead of big fixtures. "
        "Totals swing with weather/referee tendencies. Watch international windows: clubs "
        "lose players to national duty, a classic systematic mispricing."
    )
