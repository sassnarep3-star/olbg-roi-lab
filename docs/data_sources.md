# Public data sources per sport

Everything here is public/freely accessible (check each site's terms; many
free tiers limit request volume). Odds data: The Odds API has a free tier
(500 requests/month, no card) — `export ODDS_API_KEY=...` then
`python -m olbg_roi fetch-odds --source the-odds-api --sport tennis`.

| Sport | Source | URL | What you get | Notes |
|---|---|---|---|---|
| All | The Odds API | the-odds-api.com | aggregated bookmaker odds (h2h, spreads, totals) | free key; ~500 req/mo |
| Tennis | Tennis-Data.co.uk | tennis-data.co.uk | match odds + stats per year (ATP/WTA) | free xlsx downloads |
| Tennis | Jeff Sackmann | github.com/JeffSackmann | match charts, point-level data | public repos |
| Snooker | snooker.org | snooker.org | results & fixtures | lightweight pages, easy to parse |
| Snooker | CueTracker | cuetracker.net | historic results, H2H, centuries | scrape politely |
| Gaelic | GAA | gaa.ie | fixtures & results (football + hurling) | official |
| Gaelic | RTÉ Sport | rte.ie/sport/gaa | results archive | |
| Cricket | Cricsheet | cricsheet.org | ball-by-ball match data | CC0 licensed |
| Cricket | ESPNcricinfo | espncricinfo.com | scorecards, rankings | |
| Rugby U | ESPN Scrum | espn.co.uk/rugby | results archive | |
| Rugby U | World Rugby | world.rugby/rankings | official team ratings | |
| Rugby L | NRL.com | nrl.com | results & stats | official |
| Rugby L | Rugby League Project | rugbyleagueproject.org | historic results | |
| Basketball | NBA Stats API | stats.nba.com | box scores, advanced stats | public endpoints |
| Basketball | balldontlie | balldontlie.io | NBA data API | free, no key |
| F1 | OpenF1 | openf1.org | laps, positions, weather | free open API |
| F1 | FastF1 | github.com/theOehrly/Fast-F1 | timing data python package | |
| Darts | PDC | pdc.tv | results, averages, checkouts | official |
| Darts | Darts Orakel | dartsorakel.com | player stats | |
| Baseball | MLB Stats API | statsapi.mlb.com | box scores, schedules, pitchers | free, no key |
| Baseball | Statcast | baseballsavant.mlb.com | tracking data | public |
| Greyhound | Greyhound-Data | greyhound-data.com | results, times, form | some paywalled |
| Greyhound | Racing Post | racingpost.com | results, form, going | free tier |
| Greyhound | GBGB | gbgb.org.uk | official race results | |

## Expected data formats in this repo

**Matches CSV** (`data/raw/{sport}/matches.csv`) — historical results:

```csv
date,event,player_a,player_b,score_a,odds_a,odds_b,home_a,home_b
2023-01-16,Australian Open,R.Nadal,M.Berrettini,1,1.35,3.25,,
```

`score_a`: `1` = player_a won, `0` = player_b won, `0.5` = draw (baseball run
line pushes, Test cricket draws…). `home_a/home_b`: optional `1`/`0` flags.

**Fixtures CSV** (`data/raw/{sport}/fixtures.csv`) — upcoming events for `predict`:

```csv
date,event,player_a,player_b,odds_a,odds_b
2026-08-03,ATP 500,M.A,A.B,1.80,2.00
```

## OLBG data

OLBG is an odds-comparison and tipster site with no official public API.
Legitimate uses:

- **Reference for market coverage**: OLBG lists which bookmakers price each
  market — useful for knowing where to find liquidity.
- **Tipster/community signals** (research only): OLBG tips pages show consensus
  picks; treat as a sentiment feature, never as ground truth.
- **Your own CSV exports**: if you have a licence or export, drop files into
  `data/raw/{sport}/` and they flow through the same pipeline.

Do **not** scrape OLBG at volume — it breaches their terms and gets IP-blocked.
The same bookmaker odds are available via The Odds API / OddsJam (paid) /
bookmaker affiliate feeds.
