# Dota2 Fantasy Stats

A React + TypeScript + Vite frontend backed by build-time Python data
pipelines for Dota 2 Fantasy analysis. The current published dataset is TI15
Fantasy player performance based on TI14, EWC 2026 and TI14 matches from OpenDota.

https://dota2-fantasy-stats.netlify.app/

pc:

<img width="831" height="550" alt="屏幕截图 2026-08-16 213224" src="https://github.com/user-attachments/assets/12ddb79d-2ec5-431c-92a1-bd3ae1c0045c" />

mobile:

<img width="252" height="550" alt="屏幕截图 2026-08-17 092455" src="https://github.com/user-attachments/assets/7c3a19d3-8a59-4040-a0bb-c2913dc856b2" />

<img width="252" height="550" alt="屏幕截图 2026-08-17 092534" src="https://github.com/user-attachments/assets/cdc82bd8-69b7-4589-89de-9ad93de176fb" />




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
