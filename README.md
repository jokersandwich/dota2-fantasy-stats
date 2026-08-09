# Dota2 Fantasy Stats

A React + TypeScript + Vite frontend backed by build-time Python data
pipelines for Dota 2 Fantasy analysis. The current published dataset is TI15
Fantasy player performance based on EWC 2026 matches from OpenDota league
`19785`, while including only players listed in the independent TI15 roster
configuration. The project name is tournament-neutral so additional TI14 and
future TI15 datasets can be added without renaming the application again.

https://ti15-ewc-stats.netlify.app/

pc:

<img width="831" height="550" alt="ti15-ewc-stats-pc" src="https://github.com/user-attachments/assets/a637d237-4fc1-4a9f-8ffb-a7d6fcb75094" />


mobile:

<img width="252" height="550" alt="ti15-ewc-stats-mobile" src="https://github.com/user-attachments/assets/033e42a3-29cb-44a4-b50f-d513d73e5b43" />
<img width="252" height="550" alt="ti15-ewc-stats-mobile-2" src="https://github.com/user-attachments/assets/d9eb7f9e-7856-41c9-acd3-72a3364c11f1" />



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
