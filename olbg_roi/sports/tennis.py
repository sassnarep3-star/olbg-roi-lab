"""Tennis — the reference sport with a full working pipeline + demo data."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class TennisStrategy(H2HSportStrategy):
    key = "tennis"
    display_name = "Tennis (ATP/WTA)"
    status = "reference (demo-ready)"
    elo_k = 120.0       # dynamic K: fast convergence for new players,
    elo_k_min = 25.0    # settles to a low-noise floor once rated

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "main value market"),
        MarketSpec("Set Betting", "exotic", "needs set-level model (M3)"),
        MarketSpec("Games Handicap", "handicap", "needs game-level model (M3)"),
        MarketSpec("Over/Under Games", "totals", "needs game-level model (M3)"),
    ]

    data_sources = [
        DataSourceSpec("Tennis-Data.co.uk", "http://www.tennis-data.co.uk/alldata.php",
                       "free match odds + stats xlsx per year (ATP/WTA)"),
        DataSourceSpec("Jeff Sackmann's tennis repos", "https://github.com/JeffSackmann",
                       "public match charts & point-by-point data"),
        DataSourceSpec("The Odds API", "https://the-odds-api.com", "live h2h odds (tennis_atp/tennis_wta)"),
        DataSourceSpec("ATP/WTA official", "https://www.atptour.com", "rankings & results"),
    ]

    strategy_notes = (
        "Baseline: surface-aware Elo (clay/hard/grass ratings split). Edges to chase: "
        "bookmakers lag surface form swings and fatigue/travel (late-round legs, "
        "back-to-back days); long best-of-5 matches compress variance toward true "
        "ability; retirement risk is underpriced in favorites. Milestone M3 adds "
        "serve/return points won and set-level modelling."
    )
