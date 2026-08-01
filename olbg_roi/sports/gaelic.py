"""Gaelic football & hurling (GAA)."""
from .base import H2HSportStrategy, MarketSpec, DataSourceSpec, register


@register
class GaelicStrategy(H2HSportStrategy):
    key = "gaelic"
    display_name = "Gaelic Football & Hurling (GAA)"
    status = "h2h pipeline ready — needs data"
    elo_k = 40.0
    elo_home = 45.0  # strong home advantage in county games

    markets = [
        MarketSpec("Match Winner (h2h)", "h2h", "league & championship"),
        MarketSpec("Handicap (points)", "handicap", "strong margins in mismatches"),
        MarketSpec("Over/Under Points", "totals", "hurling totals are volatile"),
        MarketSpec("To Win Sam Maguire / Liam MacCarthy", "multi", "tournament winner"),
    ]

    data_sources = [
        DataSourceSpec("GAA official", "https://www.gaa.ie", "fixtures & results (football & hurling)"),
        DataSourceSpec("RTÉ Sport", "https://www.rte.ie/sport/gaa", "results archive, scores"),
        DataSourceSpec("ClubInfo", "https://www.clubinfo.gaa.ie", "club/inter-county results"),
        DataSourceSpec("The Irish Times GAA", "https://www.irishtimes.com/sport/gaa", "coverage & stats"),
    ]

    strategy_notes = (
        "County panels are small and motivation swings hugely between league and "
        "championship (teams rotate in league). Home venue advantage is strong. "
        "Championship is knock-out — intensity and first-choice selection are reliable "
        "signals there. Data is sparser/less standardised than pro sports: start with "
        "league + championship h2h only, handicap later. Separate Elo pools for football "
        "and hurling."
    )
