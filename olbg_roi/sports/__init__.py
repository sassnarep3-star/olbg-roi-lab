"""Sport registry — importing this module registers every sport strategy."""
from . import (  # noqa: F401
    baseball,
    basketball,
    cricket,
    darts,
    f1,
    gaelic,
    greyhound,
    rugby_league,
    rugby_union,
    snooker,
    tennis,
)
from .base import all_sport_keys, all_sports, get_sport, register  # noqa: F401
