# Project Overview

This repository is `dota2-fantasy-stats`, a static Dota 2 Fantasy statistics
website.

The current published dataset evaluates TI15 roster players using EWC 2026
OpenDota matches from league `19785`. The repository name is
tournament-neutral, but many current data files and reports are intentionally
TI15-specific.

The frontend uses React, TypeScript, and Vite. Python performs data collection,
field extraction, Fantasy scoring, validation, and ranking aggregation before
the frontend is built.

Do not hardcode local filesystem paths. All project paths must be repository
relative or derived from `Path(__file__)`.

# Repository Structure

- `src/`
  - React frontend.
  - `App.tsx` renders the Role Fantasy leaderboard.
  - `i18n/` contains the Chinese and English translation system.
  - `styles.css` contains the responsive esports analytics UI.
- `scripts/`
  - `fetch-ewc.py` downloads and caches OpenDota league and match payloads.
  - `process-data.py` is the older general player-statistics pipeline.
  - `fantasy/rules.py` is the central Fantasy scoring-rule definition.
  - `fantasy/scoring.py` generates per-player, per-match Fantasy scores.
  - `fantasy/rankings.py` generates individual player rankings.
  - `fantasy/role_rankings.py` generates fixed Core/Mid/Support Role Units.
  - `fantasy/test_*.py` contains the Python unit tests.
- `data/`
  - `ti15_rosters.json` is the verified TI15 roster configuration.
  - `raw/` contains regenerable OpenDota cache files and is ignored by Git.
  - `processed/player-fantasy-rankings.json` contains individual rankings.
  - `processed/role-fantasy-rankings.json` contains the 48 Role Units used by
    the current frontend.
- `public/data/`
  - `fantasy-match-scores.json` contains per-match Fantasy scoring output.
  - `player-stats.json` is output from the older general-statistics pipeline.
- `FIELD_MAPPING.md` is the authoritative audited mapping for current Fantasy
  metrics.
- `DATA_VALIDATION.md`, `RANKINGS_VALIDATION.md`, and
  `ROLE_RANKINGS_VALIDATION.md` are generated validation reports.

# Architecture

This is a build-time data pipeline, not a live API application. There is no
database and no required production backend.

The current Fantasy data flow is:

1. `scripts/fetch-ewc.py` caches OpenDota league and match JSON under
   `data/raw/`.
2. `python -m scripts.fantasy.scoring` produces
   `public/data/fantasy-match-scores.json`.
3. `python -m scripts.fantasy.rankings` produces
   `data/processed/player-fantasy-rankings.json`.
4. `python -m scripts.fantasy.role_rankings` produces
   `data/processed/role-fantasy-rankings.json`.
5. The React frontend directly imports the precomputed Role ranking JSON.

The frontend must not independently reproduce Fantasy formulas, player
averages, Role combinations, same-match joins, or best-match selection.

Treat `scripts/process-data.py` as a separate legacy/general-statistics
pipeline. Its metric definitions are not the source of truth for Fantasy
scoring. For Fantasy work, use `FIELD_MAPPING.md` and
`scripts/fantasy/rules.py`.

# Fantasy Domain Rules

Roster matching uses numeric OpenDota `account_id`. Never match players by
nickname or display name.

The fixed Fantasy roles are:

- Core: Position 1 and Position 3
- Mid: Position 2
- Support: Position 4 and Position 5

Do not create any other position combination.

Core and Support values must be built from matches shared by both fixed
members. Join exclusively by exact `matchId`; do not infer matching games from
start time, series ID, order, or game number.

For a two-player Role Unit in one match:

- `roleRawValue` is the arithmetic mean of both members' raw values.
- `roleFantasyScore` is the arithmetic mean of both members' already-calculated
  Fantasy scores.
- If either member's metric is unavailable, the whole Role metric for that
  match is unavailable.

Mid contains one Position 2 player. Its Role values equal the player's values
and must not be divided by two.

Role averages must be calculated from per-match Role values. Do not average
each member's tournament-wide personal average and then combine those
averages.

`best` always means the match with the highest Fantasy score, not the highest
raw value. The stable tie-break order is:

1. Higher Fantasy score.
2. Raw value in the metric's configured better direction.
3. Smaller `matchId`.

This distinction is essential for inverse-scored metrics such as deaths.

Individual player `average.rawValue` is the arithmetic mean of available raw
observations. Its Fantasy score is recalculated through the shared scoring
engine in `scripts/fantasy/scoring.py`.

Role `average.fantasyScore` is the arithmetic mean of valid per-match Role
Fantasy scores.

All scoring constants and formulas belong in `scripts/fantasy/rules.py`.
Never scatter scoring constants through processors, tests, or frontend code.
Do not change Fantasy rules unless the user explicitly requests it.

The current engine calculates base Fantasy scores only. It does not include
banner quality, banner traits, coach-title bonuses, or other modifiers.

# Data Integrity Rules

Never convert missing, invalid, unavailable, or quarantined values to zero.

A genuine source value of zero is valid and distinct from unavailable data.
Unavailable per-metric values must remain `null` with the corresponding
availability state.

Exclude unavailable observations from averages and record the number of valid
observations as `validGames`.

If every observation for a metric is unavailable, both `best` and `average`
must be `null`.

Do not emit NaN, Infinity, undefined, or invalid JSON numbers.

Respect parsed-replay requirements defined by the central Fantasy rules. Do
not use parsed-only fields when the match is not confirmed as parsed.

Important audited Fantasy mappings include:

- Creep score: `last_hits + denies`
- Observer wards: `obs_placed` only
- Rune pickups: `rune_pickups`
- Roshan kills: `roshans_killed`
- Teamfight participation: the OpenDota 0-1 ratio
- Stun duration: `stuns`, in seconds
- Smokes: `item_uses.smoke_of_deceit`
- Tormentor kills: `killed.npc_dota_miniboss`, currently medium reliability

Do not substitute similarly named fields without another real-payload audit.

Madstones, watchers, and lotuses currently remain unavailable in the EWC
Fantasy dataset. Do not infer them from unconfirmed proxy fields.

Negative parser anomalies, such as invalid negative stun duration, must be
quarantined as unavailable rather than clamped to zero.

Current TI15 dataset invariants are:

- 16 roster teams
- 5 starters per team
- 80 roster players
- Positions 1 through 5 exactly once per team
- 48 Role Units: one Core, one Mid, and one Support for each team

Generated JSON and validation reports should be regenerated through their
Python modules rather than manually edited.

# Frontend Rules

The current leaderboard reads
`data/processed/role-fantasy-rankings.json`.

Do not reconstruct Role Units from `player-fantasy-rankings.json` in the
frontend.

The performance modes are `best` and `average`, with `average` as the default.
All metric display and sorting must use the selected mode.

Metric sorting uses the selected value's `fantasyScore`, not `rawValue`.
Unavailable values always sort last.

Keep the shared metric-value selector as the single access path for
best/average display values. Do not duplicate mode-selection conditionals
across components.

`firstBlood.average.rawValue` and `teamfightParticipation.rawValue` are stored
as 0-1 ratios and are converted to percentages only in the formatting layer.

Do not modify data processing or Fantasy scoring as part of ordinary UI work.
Preserve the existing high-density, dark esports analytics design unless a
redesign is explicitly requested.

Maintain desktop and mobile behavior, including sticky identity columns,
horizontal metric scrolling, sortable headers, Role filters, and the
best/average switch.

# Localization

The supported languages are:

- `zh-CN`, the default
- `en`

Translations belong in `src/i18n/translations.ts`. Avoid language conditionals
or duplicated translated strings inside React components.

Language state and persistence are managed by `src/i18n/useLanguage.ts`.
The current localStorage key is `dota2-fantasy-language`.

Changing the language must update `document.documentElement.lang`, the
document title, and the meta description without reloading the page or
resetting filters, sorting, or performance mode.

Internal metric keys and Role keys remain English and must not be localized.

Team names and player IDs always remain in their official English/original
form. Do not translate or transliterate them.

Chinese Fantasy metric labels must continue to use the approved translations
already stored in the translation table. GPM remains `GPM` in both languages.

# Build and Test Commands

The repository declares pnpm as its package manager.

Install and run the frontend with:

```powershell
pnpm install
pnpm run dev
```

After frontend or TypeScript changes, run at minimum:

```powershell
pnpm run build
```

`npm run build` invokes the same package script and may be used when explicitly
requested. The build runs TypeScript project compilation followed by the Vite
production build. Netlify publishes `dist/`.

Optional standalone TypeScript validation:

```powershell
pnpm run typecheck
```

Run all Python unit tests with:

```powershell
python -B -m unittest discover -s scripts/fantasy -p "test_*.py"
```

After Fantasy data, scoring, ranking, or Role aggregation changes, run the
Python tests and the relevant complete pipeline modules:

```powershell
python -m scripts.fantasy.scoring
python -m scripts.fantasy.rankings
python -m scripts.fantasy.role_rankings
```

Review the regenerated validation reports and confirm that they pass before
treating a data-layer change as complete.

Only run `scripts/fetch-ewc.py` when network retrieval or raw-cache refresh is
actually required. Preserve cached raw data unless an explicit refresh is
requested.

# Git / Change Safety

Inspect `git status` before starting code changes. Preserve existing user
changes and avoid overwriting unrelated work.

Do not use `git reset --hard`, force checkout, force push, rebase published
history, or otherwise rewrite Git history unless the user explicitly requests
and approves that exact operation.

Do not push, create releases, or change remotes unless explicitly requested.

Do not commit:

- `.env` files or credentials
- API keys or access tokens
- `node_modules/`
- `dist/`
- `.netlify/`
- Python caches
- local editor files
- regenerable raw OpenDota JSON caches
- machine-specific absolute paths

Do not mechanically rename every TI15 reference when changing repository or
product branding. Keep TI15-specific roster, dataset, report, and page
references when they describe actual TI15 data.

# Do Not

- Do not match players by nickname.
- Do not invent OpenDota field names.
- Do not treat unavailable data as zero.
- Do not calculate Role combinations in React.
- Do not select best performance with `max(rawValue)`.
- Do not join Role members by anything other than exact `matchId`.
- Do not duplicate Fantasy formulas outside the central rule and scoring
  modules.
- Do not use the older `process-data.py` mappings as Fantasy scoring rules.
- Do not manually edit generated ranking JSON to change results.
- Do not translate team names, player IDs, metric keys, or Role keys.
- Do not change scoring rules during UI or localization work.
- Do not broaden a requested change into unrelated data, scoring, or UI work.
