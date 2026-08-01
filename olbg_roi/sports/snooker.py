"""Snooker."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class SnookerStrategy(H2HSportStrategy):
    key = "snooker"
    display_name = "Snooker"
    status = "h2h pipeline ready — needs data"
    elo_k = 36.0

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "main value market"),
        MarketSpec("Frame Handicap", "handicap", "needs frame-level model (M3)"),
        MarketSpec("Total Frames Over/Under", "totals", "needs frame-level model (M3)"),
        MarketSpec("Tournament Winner", "multi", "long-horizon, high variance"),
    ]

    data_sources = [
        DataSourceSpec("snooker.org", "https://www.snooker.org", "results & fixtures, RSS/API-ish"),
        DataSourceSpec("CueTracker", "https://cuetracker.net", "historic results, H2H, century stats"),
        DataSourceSpec("World Snooker Tour", "https://www.wst.tv", "official results & rankings"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "h2h odds when snooker events listed"),
    ]

    strategy_notes = (
        "Format length is king: best-of-19+ (Worlds, UK) favour class and make Elo more "
        "predictive; best-of-7 qualifiers are coin flips with fat margins. Add break-building "
        "form (centuries per match) and CueTracker H2H. Watch for calendar congestion: "
        "players entering several events in a week. Tournament-winner markets are soft "
        "because bookmakers spread probability thinly across 128-player fields."
    )
