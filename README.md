# TI15 Fantasy — EWC 2026 Player Stats

A React + TypeScript + Vite frontend backed by a build-time Python data
pipeline. The pipeline uses EWC 2026 Dota 2 matches from OpenDota league
`19785`, while including only players listed in the independent TI15 roster
configuration.

## Local setup

```powershell
pnpm install
pnpm run dev
```

Build for Netlify with `pnpm run build`. Netlify configuration is included in
`netlify.toml`.

See `data/README.md` for the data workflow and `data/METRICS.md` for the audited
OpenDota field mappings. The roster file intentionally starts
in `draft` status and empty so unverified team/player identities are never
silently shipped.
