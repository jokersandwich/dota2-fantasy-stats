# Dota2 Fantasy Stats

A React + TypeScript + Vite frontend backed by build-time Python data
pipelines for Dota 2 Fantasy analysis. The current published dataset is TI15
Fantasy player performance based on EWC 2026 and TI14 matches from OpenDota.

https://dota2-fantasy-stats.netlify.app/

pc:

<img width="831" height="550" alt="pc" src="https://github.com/user-attachments/assets/ebcb0087-9588-4089-926f-0306125f153d" />



mobile:

<img width="252" height="550" alt="mobile1" src="https://github.com/user-attachments/assets/c8ee2e3c-f3aa-408d-b3b3-e2b14ddd1ced" />
<img width="252" height="550" alt="mobile2" src="https://github.com/user-attachments/assets/4568a91f-0d3d-4d92-997c-b3fdd93756f1" />





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
