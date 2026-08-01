"""Greyhound racing (multi-outcome sport — planned M6)."""
from .base import MultiOutcomeSportStrategy, MarketSpec, DataSourceSpec, register


@register
class GreyhoundStrategy(MultiOutcomeSportStrategy):
    key = "greyhound"
    display_name = "Greyhound Racing"
    status = "planned (multi-outcome)"

    markets = [
        MarketSpec("Race Winner", "multi", "6-runner softmax over form ratings"),
        MarketSpec("Forecast (exacta)", "exotic", "two-dog finish — very soft"),
        MarketSpec("Trap Number", "multi", "box-bias plays"),
        MarketSpec("To Be Placed", "multi", "top-2/top-3 finish"),
    ]

    data_sources = [
        DataSourceSpec("Greyhound-Data", "https://www.greyhound-data.com", "historic results, times, form"),
        DataSourceSpec("Racing Post", "https://www.racingpost.com", "results, form, going"),
        DataSourceSpec("GBGB", "https://www.gbgb.org.uk", "official race results"),
        DataSourceSpec("The Greyhound Star", "https://www.greyhoundstar.co.uk", "news & form analysis"),
    ]

    strategy_notes = (
        "Six runners per race → model a softmax over per-dog form ratings built from "
        "graded results, times adjusted for track going (soft/fast), and kennel form. "
        "Box/trap bias is track- and distance-specific — measure it per track from "
        "historical win rates by trap. Grade movement (up/down in class) is a strong "
        "signal. Most deep data is paywalled; OLBG tips pages + Racing Post free results "
        "are the accessible starting point. High turnover, small edges, big variance — "
        "stake discipline is everything."
    )
