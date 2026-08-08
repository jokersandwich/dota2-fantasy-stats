# TI15 Fantasy — EWC 2026 Player Stats

A React + TypeScript + Vite frontend backed by a build-time Python data
pipeline. The pipeline uses EWC 2026 Dota 2 matches from OpenDota league
`19785`, while including only players listed in the independent TI15 roster
configuration.
<img width="1917" height="1268" alt="ti15-ewc-stats-pc" src="https://github.com/user-attachments/assets/a637d237-4fc1-4a9f-8ffb-a7d6fcb75094" />
<img width="438" height="953" alt="ti15-ewc-stats-mobile" src="https://github.com/user-attachments/assets/033e42a3-29cb-44a4-b50f-d513d73e5b43" />
<img width="436" height="952" alt="ti15-ewc-stats-mobile-2" src="https://github.com/user-attachments/assets/d9eb7f9e-7856-41c9-acd3-72a3364c11f1" />



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
