# M2 — Real tennis data + first honest backtest (in progress)

## Goal
Replace synthetic `tennis_demo.csv` with real historical ATP results (and
optionally WTA) from public sources, then run the first **honest** (no
planted bias) walk-forward backtest.

## Real data sources identified

1. **tennis-data.co.uk** (`http://www.tennis-data.co.uk/`)
   - Per-year .xlsx / .csv files (ATP from 2000, WTA from 2007).
   - Columns: Date, Tournament, Surface, Round, Best of, Winner, Loser,
     WRank, LRank, WPts, LPts, W1-L5, Wsets-Lsets, plus bookmaker odds
     (UBL, MaxW, AvgW, etc.).
   - License: free download, acknowledged sources (Xscores, ATPtennis, etc.).

2. **Jeff Sackmann GitHub** (`github.com/JeffSackmann`)
   - Point-level charts, match-level data.
   - Useful for M3 feature engineering (serve %, break-point conversion).

3. **Kaggle mirrors** (e.g. `jordangoblet/atp-tour-20002016`)
   - Pre-formatted CSV; useful for quick validation but prefer original.

## Adapter added (`olbg_roi/data/tennis_converter.py`)

Reads the standard `tennis-data.co.uk` CSV format and writes repo-standard:
`date, event, player_a, player_b, score_a, odds_a, odds_b`.

- `player_a` mapped to `Winner` (so `score_a` = 1 for wins) to keep the
  positive-score convention consistent with `tests/test_demo.py`.
- Odds preference: `AvgW` / `AvgL` first (most representative book average),
  then `MaxW` / `MaxL`, then `UBL`.
- `surface` preserved as optional column.

Usage:
```bash
python -m olbg_roi.data.tennis_converter \
    --in data/raw/tennis/2024.csv \
    --out data/raw/tennis/2024_repo.csv
```

## Next steps for M2

- [ ] Download at least one full season (e.g. 2024 ATP) from tennis-data.co.uk.
- [ ] Convert with `tennis_converter.py`.
- [ ] Update `docs/data_sources.md` with download instructions.
- [ ] Modify `tests/test_demo.py` to keep synthetic demo separate from real data.
- [ ] Run `python -m olbg_roi backtest --sport tennis --data data/raw/tennis/2024_repo.csv`.
- [ ] Expect lower (possibly negative) ROI on real data — document honestly.
- [ ] If ROI is poor, apply the market-agreement filter (`min_implied_prob=0.5`)
      and dynamic-K Elo settings from M0 (documented in `config/config.json`).

## Honesty checklist (must do before claiming M2 complete)

- [ ] README updated: demo data clearly labeled synthetic; real-data results clearly labeled.
- [ ] `reports/` files include a note: "Real tennis data from tennis-data.co.uk (2024); ROI may differ from synthetic demo."
- [ ] `.gitignore` keeps downloaded `.xlsx` out of the repo.
- [ ] No synthetic bias injected into real data pipeline.
