"""Darts (PDC)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class DartsStrategy(H2HSportStrategy):
    key = "darts"
    display_name = "Darts (PDC)"
    status = "h2h pipeline ready — needs data"
    elo_k = 40.0

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "main value market"),
        MarketSpec("Legs Handicap", "handicap", "leg-level model (M3)"),
        MarketSpec("Total 180s", "totals", "needs player 180-rate data"),
        MarketSpec("Correct Score (sets/legs)", "exotic", "very soft"),
    ]

    data_sources = [
        DataSourceSpec("PDC", "https://www.pdc.tv", "official results, averages, checkouts"),
        DataSourceSpec("Darts Orakel", "https://www.dartsorakel.com", "detailed player stats"),
        DataSourceSpec("DartConnect", "https://www.dartconnect.com", "live scoring data"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "darts odds when listed"),
    ]

    strategy_notes = (
        "Three-dart average + checkout % are strong, fast-moving signals the market "
        "underweights between TV events. Format length is critical: best-of-11 floor events "
        "are swingy; Worlds/Slam best-of-35 favour elite averages. Floor vs TV form "
        "diverges — price players on the stage type. Elo on match results is a good "
        "baseline; M3 adds rolling 3-dart averages and checkout-pressure stats."
    )
