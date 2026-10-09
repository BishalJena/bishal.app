# bishal.app — todo

Details and acceptance criteria: [plan.md](plan.md)

## Phase 0 — Housekeeping
- [ ] T0 Merge `waitlist-on-bishal-app` → `main` in apple-cta-websites (confirm first)

## Phase 1 — Sync catalogue ↔ Lotus apps
- [ ] T1 `build.py` emits `public/lotus-apps.json` → live at bishal.app/lotus-apps.json
- [ ] T2 Catalogue renders the 7 Lotus apps from the manifest (real icons, same-origin previews)

### Checkpoint A — catalogue in sync, review with user

## Phase 2 — Pages + analytics
- [ ] T3 Dashboard: Pages project via Connect to Git (output `public`) + enable Web Analytics
- [ ] T4 Move bishal.app + www from Worker `bishal-app` → Pages; verify `/lotus-*` still works; delete Worker + `wrangler.jsonc`
- [ ] T5 Beacon in Lotus page template (token from T3)

### Checkpoint B — push = deploy, analytics on all pages, waitlists unaffected

## Phase 3 — Launch polish
- [ ] T6 Favicon, touch icon, OG image + meta, canonical
- [ ] T7 Security headers via `public/_headers`
- [ ] T8 READMEs in both repos
- [ ] T9 (optional) Workers Builds auto-deploy for `lotus-waitlists`

### Checkpoint C — launched
