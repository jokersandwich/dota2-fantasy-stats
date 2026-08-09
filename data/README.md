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

## Fantasy multi-dataset pipeline

The published default dataset is `ti15-ewc-2026`. Its three independent
references are:

- roster source: `data/rosters/ti15-2026.json`
- match source: `data/config/match-sources/ewc-2026-opendota.json`
- shared ruleset: `ti15-base-v1`, backed directly by `scripts/fantasy/rules.py`

Dataset registration and composition live under `data/config/datasets/`.
Generated artifacts and validation reports are namespaced by immutable
`datasetId`:

```text
data/generated/datasets/<datasetId>/
reports/<datasetId>/
public/data/datasets/<datasetId>/
```

Generate and validate the default dataset with:

```powershell
python -m scripts.fantasy.scoring
python -m scripts.fantasy.rankings
python -m scripts.fantasy.role_rankings
python -m scripts.fantasy.semantic_compare compare
python -m scripts.fantasy.publish_dataset
```

`publish_dataset` updates the current legacy compatibility files only after
the TI15-EWC candidates match the frozen semantic baseline. The React frontend
continues to read `data/processed/role-fantasy-rankings.json`; it does not yet
perform dataset switching.

Namespaced player-ranking artifacts use `source.rosterPlayers`. The TI15-EWC
legacy player-ranking alias is converted during publication to the historical
`source.ti15Players` field, so the generic schema does not carry both names.
Validation profiles use exact dataset-specific counts; only
`playersWithoutGames` may be zero.
