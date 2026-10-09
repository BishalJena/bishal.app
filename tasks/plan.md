# Implementation Plan: bishal.app — catalogue ↔ Lotus apps sync, Pages + analytics

## Overview
bishal.app is two projects sharing one domain:

| Path | Repo | Runs as | Purpose |
|---|---|---|---|
| `/` | `BishalJena/bishal.app` (this repo) | Worker `bishal-app` (static assets) → **moving to Pages** | Catalogue: sidebar list + live preview |
| `/lotus-*` | `BishalJena/apple-cta-websites` | Worker `lotus-waitlists` (route `bishal.app/lotus-*`, D1 `waitlist-db`) | 7 app landing pages + waitlist API |

Goals: (1) the catalogue lists the real Lotus apps and stays in sync automatically,
(2) the main site moves to Cloudflare Pages with GitHub auto-deploy and one-click Web Analytics,
(3) analytics covers both `/` and `/lotus-*`, (4) finish launch polish.

## Current state (verified 2026-10-09)
- `https://bishal.app/` → catalogue (200). `/lotus-g-1/`, `/lotus-c-1/`, `/lotus-e-3/` → Lotus sites (200).
  `/lotus-g-1/api/join` → 405 on GET (API alive). Both Workers coexist correctly today.
- Catalogue `public/apps.js` = 7 **placeholder** apps; Lotus apps are not listed.
- `apple-cta-websites`: live code is on branch `waitlist-on-bishal-app` (85 files ahead of `main`, pushed, not merged).
  No analytics beacon in Lotus pages. README already assumes "main site = separate Pages project".
- Each Lotus app's metadata lives in `tools/site-builder/apps/lotus_*.py` (`APP = {name, title, icon{from,to,glyph}, …}`);
  each site ships `public/<slug>/assets/app-icon.svg`.
- Both repos public. Wrangler OAuth can deploy Workers/Pages but **cannot**: connect Git, toggle Web
  Analytics, or mint API tokens → one dashboard session is unavoidable.

## Architecture Decisions
- **Single source of truth for apps = the Lotus site-builder.** `build.py` also emits
  `public/lotus-apps.json` (name, slug, tagline, colors, url, icon path). Because the Worker route is
  `bishal.app/lotus-*`, that file is served at `https://bishal.app/lotus-apps.json` with no route change.
  The catalogue fetches it at runtime → adding/renaming an app in apple-cta-websites updates the
  catalogue on its next deploy, with no edit in this repo.
- **Same-origin previews.** Lotus sites live on bishal.app, so the catalogue iframe never hits
  `X-Frame-Options` problems; `embed: false` is only for future third-party links.
- **Main site → Pages, no Functions.** Created in the dashboard with *Connect to Git* (a CLI "direct upload"
  project can never be Git-connected). Build command none, output dir `public`. Web Analytics via the
  Pages toggle.
- **Lotus pages get the beacon snippet** (same Web Analytics site token). The Pages toggle only injects
  into Pages responses, not into the `lotus-waitlists` Worker's responses.
- **Sync first, then move hosts**: Phase 1 ships through the current Worker so the content change and the
  hosting change are verified separately.

## Dependency graph
```
T0 Merge apple-cta-websites branch → main
   │
T1 build.py emits /lotus-apps.json ──► T2 Catalogue reads manifest ──► Checkpoint A
                                                                          │
T3 Dashboard: Pages (Connect to Git) + Web Analytics  ─────────────────────┤
   │                                                                      │
   ├─► T4 Move bishal.app + www from Worker → Pages; delete Worker ────────┤
   └─► T5 Beacon in Lotus pages (needs token from T3)                     │
                                                                Checkpoint B
                                                                          │
           T6 Favicon/OG/canonical · T7 _headers · T8 READMEs · T9 Lotus auto-deploy (optional)
                                                                          │
                                                                Checkpoint C
```

---

## Phase 0 — Housekeeping

### Task 0: Make `main` match what's live in apple-cta-websites
**Description:** Merge `waitlist-on-bishal-app` into `main` (fast-forward/PR) so the default branch is the
deployed code. Needed before anything auto-deploys from `main`.

**Acceptance criteria:**
- [ ] `origin/main` contains commit `097d1a5` (current branch head)
- [ ] No uncommitted changes lost (`.playwright-mcp/`, `.wrangler/` stay ignored)

**Verification:** `git log origin/main -1` = `097d1a5` (or merge commit containing it); live sites unchanged
**Dependencies:** None · **Files:** none (git only) · **Scope:** XS
**Note:** confirm with user — another session may still be working on that branch.

## Phase 1 — Sync catalogue ↔ Lotus apps

### Task 1: Lotus builder emits an app manifest
**Description:** Extend `tools/site-builder/build.py` to write `public/lotus-apps.json` after building:
`[{ slug, name, tagline: APP.title, colors: [icon.from, icon.to], url: "/<slug>/", icon: "/<slug>/assets/app-icon.svg" }]`,
in APPS.md order. Rebuild, commit, `npx wrangler deploy` from apple-cta-websites.

**Acceptance criteria:**
- [ ] `https://bishal.app/lotus-apps.json` returns 200, `application/json`, 7 entries
- [ ] Rebuilding with an app removed/added changes the manifest accordingly
- [ ] Lotus pages and waitlist API unaffected

**Verification:** `curl` the manifest (via `--resolve` @1.1.1.1); spot-check 2 slugs; POST test to a waitlist returns 400 for bad email
**Dependencies:** T0 · **Files:** `tools/site-builder/build.py`, `public/lotus-apps.json` (generated) · **Scope:** S

### Task 2: Catalogue renders from the manifest
**Description:** In this repo, `index.html` fetches `/lotus-apps.json` and renders rows with the real app
icons (`<img>` of each `app-icon.svg`) instead of glyphs; delete the placeholder list in `apps.js`
(keep it only for optional extra/external entries, empty by default). Show a skeleton while loading and a
friendly empty state if the fetch fails. Ship via current Worker deploy.

**Acceptance criteria:**
- [ ] Live catalogue lists the 7 Lotus apps with real names, taglines and icons
- [ ] Selecting one previews `https://bishal.app/lotus-x/` in the frame (same origin, no blank frames)
- [ ] Deep links work (`#lotus-g-1`), arrow-key navigation still works
- [ ] Local dev (no manifest) shows the empty state, not a JS error

**Verification:** Browser click-through desktop + 390px; console clean; Lighthouse a11y ≥ 95
**Dependencies:** T1 · **Files:** `public/index.html`, `public/apps.js`, `public/styles.css` · **Scope:** M

### Checkpoint A — catalogue in sync
- [ ] Catalogue shows the 7 Lotus apps from the manifest, previews load
- [ ] Review with user before moving hosting

## Phase 2 — Pages + analytics

### Task 3: Dashboard session (user, or Claude driving Chrome with approval)
**Description:** One visit, three clicks-worth:
1. Workers & Pages → Create → Pages → **Connect to Git** → `BishalJena/bishal.app`, branch `main`,
   framework none, build command empty, output directory `public`. Project name `bishal-app-pages`
   (name `bishal-app` is taken by the Worker until T4).
2. Project → Metrics → **Enable Web Analytics**; copy the site token (for T5).
3. *(Optional, for T9)* Workers & Pages → `lotus-waitlists` → Settings → Builds → Connect `apple-cta-websites`.

**Acceptance criteria:**
- [ ] Pages project builds `main` successfully to `*.pages.dev`
- [ ] Web Analytics enabled; token recorded (public value, safe to commit)

**Verification:** `<project>.pages.dev` serves the catalogue; `npx wrangler pages project list` shows it
**Dependencies:** Checkpoint A · **Files:** none · **Scope:** XS

### Task 4: Move the domain to Pages and retire the Worker
**Description:** Remove the `routes` custom domains from `wrangler.jsonc` and redeploy (or delete the
`bishal-app` Worker) to free `bishal.app` + `www.bishal.app`; add both as Pages custom domains (dashboard
or Pages domains API); delete `wrangler.jsonc`; update memory notes (deploy = push).

**Acceptance criteria:**
- [ ] `bishal.app/` and `www.bishal.app/` served by Pages (response has `cf-ray`, Pages deployment matches latest commit)
- [ ] **`bishal.app/lotus-*` still served by `lotus-waitlists`** (Worker route must win over the Pages domain)
- [ ] Worker `bishal-app` deleted; `wrangler.jsonc` removed from repo

**Verification:** `curl` `/`, `/lotus-g-1/`, `/lotus-apps.json`, waitlist POST; a test push auto-deploys to Pages
**Dependencies:** T3 · **Files:** `wrangler.jsonc` (delete), `README.md` · **Scope:** S
**Risk:** a few minutes of downtime on `/` while Pages issues the cert — acceptable while site is pre-launch.

### Task 5: Analytics on the Lotus pages
**Description:** Add the Web Analytics beacon (`static.cloudflareinsights.com/beacon.min.js`, token from T3)
to the shared page template in `build.py`; rebuild; deploy lotus-waitlists.

**Acceptance criteria:**
- [ ] Every `/lotus-*/` page includes the beacon; catalogue gets it from the Pages toggle
- [ ] Web Analytics shows visits for `/` and `/lotus-*` paths

**Verification:** Network panel shows `cdn-cgi/rum` 204 on both; dashboard path filter shows both
**Dependencies:** T3 · **Files:** `tools/site-builder/build.py` (+ generated `public/`) · **Scope:** S

### Checkpoint B — hosting + analytics
- [ ] Push to `bishal.app` main → live in ≤2 min, no manual step
- [ ] `/lotus-*` + waitlist API unaffected
- [ ] Analytics recording on all pages

## Phase 3 — Launch polish

### Task 6: Favicon, touch icon, OG image, canonical
- [ ] Tab icon + iOS touch icon; link previews (iMessage/Slack/X) show title/description/image; `<link rel="canonical" href="https://bishal.app/">`
- Verify: fetch live HTML; OG debugger. **Files:** `public/index.html`, `public/favicon.svg`, `public/apple-touch-icon.png`, `public/og.png` · **Scope:** S

### Task 7: Security headers (`public/_headers`, Pages-native)
- [ ] `nosniff`, `Referrer-Policy`, `Permissions-Policy`, CSP allowing `frame-src 'self' https:`, `script-src 'self' 'unsafe-inline' static.cloudflareinsights.com`, `connect-src 'self' cloudflareinsights.com`
- Verify: `curl -sI`; console has no CSP violations; previews + beacon work. **Depends:** T4, T5 · **Scope:** XS

### Task 8: READMEs
- [ ] This repo: what it is, that apps come from `/lotus-apps.json`, deploy = push
- [ ] apple-cta-websites README: manifest + "main site is the Pages project `bishal-app-pages`"
- **Scope:** XS

### Task 9 (optional): Auto-deploy the Lotus Worker
- [ ] Workers Builds connected for `lotus-waitlists` (T3 step 3), build command `python3 tools/site-builder/build.py`, deploy `npx wrangler deploy`
- Verify: push to apple-cta-websites main → new Worker version; manifest + catalogue update without touching this repo

### Checkpoint C — launched
- [ ] Both repos auto-deploy on push; catalogue updates itself from the Lotus builder
- [ ] Analytics, link previews, headers in place; console clean

## Risks and Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Pages custom domain overrides the `bishal.app/lotus-*` Worker route | **High** (waitlists down) | Verify on `pages.dev` first; after T4 immediately curl `/lotus-*` + API; rollback = re-add custom domain to Worker (`wrangler deploy` of old config) |
| Another session is mid-work on `waitlist-on-bishal-app` | Med | Ask before merging (T0); never force-push |
| Manifest fetch fails (local dev, outage) | Low | Empty state + optional static fallback in `apps.js` |
| Ad blockers block the beacon | Low | Accept; Pages/Worker metrics still count requests |
| Network DNS caching on user's LAN | Low | Verify via `dig @1.1.1.1` + `curl --resolve` |

## Open Questions
1. **T0:** OK to merge `waitlist-on-bishal-app` → `main` in apple-cta-websites? Is another session still working on it?
2. **T3:** You click through the dashboard, or I drive your Chrome?
3. **T9:** Auto-deploy the Lotus Worker too, or keep it manual for now?
4. **T6:** Favicon/OG — reuse a Lotus-style gradient icon with a "b" monogram, or something else?
