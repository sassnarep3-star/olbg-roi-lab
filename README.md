# 🎯 OLBG ROI Lab

A long-term research project to find **profitable (positive-ROI) betting strategies** for sports
covered on OLBG (Online Betting Guide), built from **publicly available data**:

Snooker · Gaelic Football & Hurling · Cricket · Rugby Union · Rugby League · Basketball ·
Formula 1 · Tennis · Darts · Baseball · Greyhound Racing

> ⚠️ **Disclaimer.** Betting involves financial risk. Nothing here guarantees profit — the
> "positive ROI" demo runs on *synthetic data with a planted bias* to prove the pipeline works.
> Real-world edge requires real data, rigorous validation, and discipline. Never bet money you
> can't afford to lose. This project is for research/educational purposes.

---

## Why this project exists

Bookmaker odds are efficient but **not perfectly calibrated**. Systematic inefficiencies
(the *favourite–longshot bias*, home-advantage mispricing, slow reactions to form/injury news,
poor markets in niche sports) create repeatable edges for a disciplined model. This repo builds,
sport by sport:

1. **Odds ingestion** — from public odds APIs and OLBG-referenced bookmakers
2. **Calibration** — strip bookmaker margin → true implied probabilities
3. **Predictive models** — baseline: surface-aware Elo; later: gradient boosting on public stats
4. **Value detection** — bet only when `model_prob > implied_prob` by a margin
5. **Staking** — fractional Kelly, capped, with bankroll & drawdown tracking
6. **Backtesting** — walk-forward ROI per sport, per market, per bookmaker
7. **Live predictions** — one CLI command to output today's value bets

## Quickstart (zero dependencies, pure Python)

```bash
cd olbg-roi-lab

# 1. Generate synthetic demo data (tennis, with a *planted* bookmaker bias)
python -m olbg_roi init-demo

# 2. Backtest the Elo baseline strategy → ROI report
python -m olbg_roi backtest --sport tennis --data data/raw/tennis_demo.csv

# 3. Train (fit) the Elo model on match history
python -m olbg_roi fit --sport tennis --data data/raw/tennis_demo.csv --out models

# 4. Generate predictions for upcoming fixtures → value bets
python -m olbg_roi predict \
  --sport tennis \
  --model models/elo_tennis.json \
  --fixtures data/raw/tennis_demo_fixtures.csv

# 5. Run the test suite
python -m unittest discover -s tests -v
```

## Architecture

```
olbg_roi/
├── cli.py            # argparse CLI: init-demo, fit, backtest, predict, fetch-odds, list-sports
├── config.py         # global config (bankroll, thresholds, Kelly params)
├── odds/
│   ├── margin.py     # overround removal: proportional / power / Shin
│   ├── model.py      # Market & Selection dataclasses, CSV/JSON loaders
│   └── sources.py    # odds ingestion adapters (The Odds API, OLBG guidance)
├── ratings/
│   └── elo.py        # pure-Python Elo model (train / predict / persist)
├── betting/
│   ├── value.py      # edge & expected-value detection
│   ├── kelly.py      # fractional Kelly staking
│   └── bankroll.py   # bankroll tracking & ROI accounting
├── backtest/
│   └── engine.py     # walk-forward backtester → CSV / JSON / Markdown reports
├── predict/
│   └── pipeline.py   # fixtures + model + odds → predictions & bet recommendations
├── sports/           # one module per sport: markets, data sources, strategy notes
└── demo/
    └── generate.py   # synthetic demo dataset generator (clearly labeled)
```

## The strategy loop (applies to every sport)

```
 public data ──► features ──► model ──► fair probability ──┐
                                                           ├─► edge = P_model − P_implied
 bookmaker odds ─► remove margin ─► P_implied ─────────────┘        │
                                                                    ▼
                                     edge ≥ threshold & odds ≥ min? ──► no ─► skip
                                                                    │ yes
                                                                    ▼
                                            fractional Kelly stake ──► backtest → ROI?
```

## Odds ingestion (updated M1)

We support **three public sources** to work around the 500-credit/month cap on The Odds API:

| Source | CLI flag | Key env var | Free tier | Workaround feature |
|---|---|---|---|---|
| The Odds API | `--source the-odds-api` | `ODDS_API_KEY` | 500 req/mo | 1-hr JSON cache (`cache/`) |
| SharpAPI | `--source sharpapi` | `SHARPAPI_KEY` | 12 req/min (17,280/day) | No card needed |
| odds-api.net | `--source odds-api-net` | `ODDS_API_NET_KEY` | Free key + mock mode | Mock mode (`_mock`) for pipeline testing |

**Rate tracker** (`.cache_requests.json`) counts requests per source and warns at 90% of free-tier limits. **Batch fetch** (`batch_fetch`) pulls multiple sports in one loop. If no key is set, adapters write clearly-tagged mock JSON so `predict` and backtests still run — see the warnings printed when running without keys. Always label synthetic results as synthetic (`docs/data_sources.md`).

## Sport status (M0 — M1 odds layer complete)

| Sport | Outcome type | Baseline model | Status |
|---|---|---|---|
| Tennis | h2h | surface Elo | ✅ **Reference impl + demo data** |
| Snooker | h2h | Elo + format-aware | 🟡 h2h pipeline ready, needs data |
| Gaelic Football/Hurling | h2h | Elo + home adv | 🟡 h2h pipeline ready, needs data |
| Cricket (Test/ODI/T20) | h2h | per-format Elo | 🟡 h2h pipeline ready, needs data |
| Rugby Union | h2h | Elo + home adv | 🟡 h2h pipeline ready, needs data |
| Rugby League | h2h | Elo + home adv | 🟡 h2h pipeline ready, needs data |
| Basketball | h2h | Elo + rest-day adj | 🟡 h2h pipeline ready, needs data |
| Darts | h2h | Elo + averages | 🟡 h2h pipeline ready, needs data |
| Baseball | h2h | Elo + SP adj | 🟡 h2h pipeline ready, needs data |
| Formula 1 | multi-outcome | softmax over ratings | 🔴 planned (M6) |
| Greyhound | multi-outcome | ratings + trap bias | 🔴 planned (M6) |

See **[docs/roadmap.md](docs/roadmap.md)** for the full long-term plan and
**[docs/data_sources.md](docs/data_sources.md)** for public data sources per sport.

## GitHub setup

```bash
# create the remote (public or private) and push:
gh repo create olbg-roi-lab --public --source . --push
# or manually:
git remote add origin https://github.com/<you>/olbg-roi-lab.git
git push -u origin main
```

## License

MIT — see [LICENSE](LICENSE).
