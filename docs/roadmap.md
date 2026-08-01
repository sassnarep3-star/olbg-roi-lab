# Roadmap — long-term plan

This is a marathon, not a sprint. Each sport gets the same treatment, one
milestone at a time. M0 (this repo) is the working skeleton with a reference
implementation on tennis.

## Milestones

| # | Milestone | Contents | Status |
|---|---|---|---|
| M0 | **Scaffold + demo pipeline** | Repo, CLI, margin removal, Elo baseline, value detection, Kelly staking, walk-forward backtester, prediction generator, synthetic demo | ✅ done |
| M1 | **Real odds ingestion** | SharpAPI + odds-api.net adapters, caching, rate tracker, mock mode, batch fetch, CLI choices updated | ✅ done (workaround: free tiers + mock) |
| M2 | **Real data + per-sport features** | Historical results per sport → h2h Elo baselines, backtested ROI per sport on real data; surface/tournament/home splits | 🟡 started (tennis adapter + source links) |
| M3 | **Feature engineering** | Sport-specific public stats (serve %, 3-dart averages, pace, SP quality, qualifying→race…), feature store, train/valid/test splits | |
| M4 | **Model upgrade** | Gradient boosting (LightGBM) on Elo + features; calibration (Platt/isotonic); Brier/log-loss evaluation; walk-forward CV | |
| M5 | **Staking & bankroll** | Kelly variants (fractional, half-Kelly, proportional), drawdown control, correlation-aware staking, bet limits | |
| M6 | **Multi-outcome sports** | F1 (race winner/podium/h2h) & greyhound (6-runner softmax, trap bias) pipelines | |
| M7 | **Live predictions & monitoring** | Scheduled data pulls, daily predictions, tracking actual results vs model, drift alerts, honest ROI ledger | |

## Per-sport plan

General approach for each sport:

1. **Ingest** historical results + odds → `data/raw/{sport}/`
2. **Fit** the h2h Elo baseline → backtest walk-forward → record ROI on real data
3. **Identify** where the baseline leaks (by market, by league, by month)
4. **Add** sport-specific public features → re-backtest → keep only what improves out-of-sample ROI
5. **Ship** per-sport prediction configs into `config/` so `olbg-roi predict` just works

### Tennis (reference — M0 done)
- Baseline: surface-aware Elo (M0). Next: Sackmann point-level data → serve/return ratings (M3).
- Targets: h2h, then games handicap & set betting once set-level model lands.

### Snooker
- M2: snooker.org results → Elo per tour. M3: centuries/match, H2H via CueTracker, format-length weighting.
- Targets: match winner; frame handicap after frame-level model.

### Gaelic (football + hurling)
- M2: GAA.ie fixtures/results → separate Elo pools, strong home adjustment. M3: league vs championship
  motivation flags, margin data for handicaps.
- Targets: match winner; handicap once margin data is in.

### Cricket
- M2: Cricsheet results per format (Test/ODI/T20) → 3 Elo pools. M3: toss/venue/weather features,
  Test 3-way draw modelling.
- Targets: match winner per format; top-batsman later (soft markets, but needs player-level model).

### Rugby Union
- M2: ESPN Scrum results → Elo with home advantage. M3: tier/referee/travel features.
- Targets: match winner, handicap, totals.

### Rugby League
- M2: NRL + Super League → Elo. M3: turnaround days, travel distance, weather → totals.
- Targets: match winner, handicap, totals.

### Basketball
- M2: balldontlie / NBA Stats API → Elo. M3: rest days, back-to-backs, pace, injury flags → moneyline + totals.
- Targets: moneyline, spread, totals.

### Darts
- M2: PDC results → Elo. M3: 3-dart average & checkout form, format length.
- Targets: match winner; legs handicap after leg-level model.

### Baseball
- M2: MLB Stats API results → Elo. M3: starting-pitcher-adjusted ratings, bullpen rest, park factors.
- Targets: moneyline; run line/totals after push handling is verified.

### Formula 1 (multi-outcome — M6)
- M2: OpenF1/FastF1 results → driver h2h Elo (pairwise markets usable early).
- M6: race-winner softmax over driver + constructor ratings; grid/qualifying features; track clusters.
- Targets: race winner, podium, driver h2h.

### Greyhound (multi-outcome — M6)
- M2: Racing Post/Greyhound-Data results → per-dog form ratings, trap-bias per track.
- M6: 6-runner softmax + graded times, going adjustments.
- Targets: race winner, places, trap plays.

## Evaluation bar (what "profitable strategy" means here)

- **Out-of-sample only**: walk-forward / time-series splits; no look-ahead bias anywhere.
- **Significance**: ROI must beat the vig with a sample size large enough that the
  confidence interval on ROI excludes ≤ 0 (binomial + bootstrap checks).
- **Drawdown**: strategy must survive a capped-fractional-Kelly bankroll simulation.
- **Transparency**: every backtest writes per-bet records; every prediction logs
  the model, inputs and stake used — the ledger is auditable.
