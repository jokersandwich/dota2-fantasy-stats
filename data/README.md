# Data pipeline

The pipeline has two independent scripts:

1. `scripts/fetch-ewc.py` reads league `19785`, caches the league response at
   `data/raw/league_19785_matches.json`, and caches each match at
   `data/raw/matches/<match_id>.json`.
2. `scripts/process-data.py` matches only configured TI15 starters by numeric OpenDota
   `account_id` and writes `public/data/player-stats.json` for the frontend.

The standard-library-only script can be run with:

```powershell
python scripts/fetch-ewc.py
python scripts/process-data.py
```

For a deterministic validation sample instead of downloading every match:

```powershell
python scripts/fetch-ewc.py --sample-size 5 --seed 20260807
python scripts/process-data.py --audit --audit-matches 5 --audit-players 10
```

Fill `data/ti15_rosters.json` after the 16 team rosters are verified. Each team
must have exactly five starters with positions 1 through 5:

```json
{
  "name": "Example Team",
  "team_id": 123,
  "players": [
    { "account_id": 123456789, "name": "Player", "position": 1 }
  ]
}
```

The display name is metadata only. Matching always uses `account_id`.

## Metric rules

- Creep score is `last_hits + denies`.
- Wards are observer plus sentry wards placed.
- Smokes are `item_uses.smoke_of_deceit` uses, not purchases.
- Percentiles use linear interpolation over per-match observations.
- A metric is marked `unavailable` with `null` values if it is missing from any
  player-match payload. A genuine reported zero remains zero.

See `data/METRICS.md` for the field-by-field reliability and parsed replay audit.
