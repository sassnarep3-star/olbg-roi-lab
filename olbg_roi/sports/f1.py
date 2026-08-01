"""Formula 1 (multi-outcome sport — planned M6)."""
from .base import MultiOutcomeSportStrategy, MarketSpec, DataSourceSpec, register


@register
class F1Strategy(MultiOutcomeSportStrategy):
    key = "f1"
    display_name = "Formula 1"
    status = "planned (multi-outcome)"

    markets = [
        MarketSpec("Race Winner", "multi", "20-driver softmax over driver+constructor ratings"),
        MarketSpec("Podium Finish", "multi", "top-3 finish probability"),
        MarketSpec("Driver H2H (qualifying/race)", "h2h", "pairwise markets — usable with h2h pipeline"),
        MarketSpec("Constructor Winner", "multi", "team-level"),
        MarketSpec("Fastest Lap", "exotic", "very soft market"),
    ]

    data_sources = [
        DataSourceSpec("OpenF1", "https://openf1.org", "free open F1 API (laps, positions, weather)"),
        DataSourceSpec("FastF1", "https://github.com/theOehrly/Fast-F1", "Python package for timing data"),
        DataSourceSpec("Ergast archive", "https://ergast.com/mrd", "historic results (frozen but mirrored)"),
        DataSourceSpec("FIA", "https://www.fia.com", "official results"),
    ]

    strategy_notes = (
        "Qualifying → race conversion is the strongest public signal (~0.7 correlation): "
        "grid position models are the backbone. Cluster circuits (street vs power vs "
        "high-degradation) because car strengths are track-specific. Race winner = softmax "
        "over driver ratings + constructor strength + grid penalty adjustments. Weather and "
        "safety-car variance cap how much edge any model can hold. Start with driver H2H "
        "markets (pairwise Elo) before race-winner multinomials."
    )
