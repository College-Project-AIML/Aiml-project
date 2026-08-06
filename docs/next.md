# Next — Near-Real-Time Scheme Updates From Live Portals

**Goal:** Pull scheme data (new schemes, deadline changes, eligibility edits, closed schemes)
from the **Karnataka Scholarship Portal (SSP)** and the **MyScheme portal** into our database
in near-real-time, and surface the changes to users.

**Plan shape (the three steps):**

1. **Connectors** — one fetcher per source that pulls the freshest public data and converts it
   into the standard raw-record shape our pipeline already understands.
2. **Change detection + sync engine** — fingerprint every fetched scheme, diff against the last
   known snapshot, and upsert *only what changed* into Postgres (classifying each change).
3. **Surface the updates** — expose an `/api/v1/updates` endpoint and a "What's New" UI so users
   can see live changes, with a path to notifications later.

---

## 0. Reality check — what the portals actually offer (verified 2026-08-05)

| Source | Public API? | Feed / sitemap? | Ground truth |
|---|---|---|---|
| **ssp.karnataka.gov.in** (State Scholarship Portal) | ❌ No public REST/JSON API | ❌ No RSS, no sitemap | ASP.NET backend; cookie sessions, `__RequestVerificationToken` anti-forgery tokens, captchas, login-gated flows. Only the **public landing pages** (`/`, `/ssppre/PreHome`, `/ssppre/PostHome`) are scrapable. Login flows are **off-limits** (legal + brittle). |
| **myscheme.gov.in** (MeitY, national) | ⚠️ Internal JSON API — undocumented, but used by the site's own React SPA | ✅ `sitemap.xml` exists (mostly static pages) | Scheme detail pages follow `/schemes/{slug}`. The real scheme/search API can be **captured from the browser DevTools network tab**. This is the single richest source. |
| **data.gov.in / karnataka.data.gov.in** | ❌ No live scholarship datasets | ❌ | Not a source for real-time updates. |

> **Implication:** "Near-real-time" means **frequent, respectful polling + change detection**, not
> push streaming. That is the industry-standard approach for government portals and is more than
> enough for this product. Deadlines/notices change daily at most; scheme catalogs change weekly.

**Why this fits our architecture:** the existing pipeline
(`normalizer → validator → dedup → PostgresLoader`) is already built exactly for this. The
`PostgresLoader` already does `ON CONFLICT (id) DO UPDATE` upserts, so re-running it is idempotent.
`apscheduler` is **already in `requirements.txt`** — the scheduler dependency exists but nothing
uses it yet. This plan activates it.

---

## Step 1 — Connector layer

### 1.1 Directory layout

```
ingestion/
  sources/
    myscheme/
      __init__.py
      client.py          # HTTP + optional Playwright fallback
      parser.py          # HTML/JSON → raw records
    karnataka_ssp/
      __init__.py
      client.py          # Playwright-driven (public pages only)
      parser.py          # DOM → raw records + notices
  sync/
    __init__.py
    fingerprint.py       # content fingerprinting (Step 2)
    change_detector.py   # diff + classification (Step 2)
    scheduler.py         # APScheduler glue (Step 2)
  pipelines/
    live_sync_pipeline.py  # orchestrates: fetch → parse → normalize → validate → dedup → upsert → record changes
```

### 1.2 MyScheme connector (`ingestion/sources/myscheme/`)

The richest source — 1000+ central + state schemes including Karnataka.

1. **Discover the real API first (5 minutes in DevTools):**
   - Open `myscheme.gov.in` → DevTools → Network tab → click through search / a scheme detail page.
   - Note the JSON endpoints and their query params (search, category, state filters, scheme slug).
   - Save a sample response to `data/raw/myscheme/sample.json` as the contract for the parser.
   - > This must be done before coding the client — endpoint paths are undocumented and change over time. I can run a browser-automation session to capture these endpoints for you.
2. **Fetch:** `client.py` calls the captured endpoints with polite headers, paginates, and writes
   raw JSON to `data/raw/myscheme/{ts}/`. Use a modest `User-Agent`, retries, and a per-domain
   rate limit (e.g. 1 req/2s) — this is a government production site.
3. **Fallback path:** if the internal API moves, fall back to Playwright rendering of the scheme
   list + detail pages and parse the DOM.
4. **Parse → raw records** (`parser.py`): each scheme becomes a record with exactly the keys our
   normalizer already consumes:
   ```python
   {
     "scheme_name": ..., "source": "myscheme.gov.in", "category": "scholarship",
     "ministry": ..., "description": ..., "eligibility": ...,
     "state": "karnataka" | "india", "link": "https://www.myscheme.gov.in/schemes/{slug}",
     "tags": [...]
   }
   ```
   Also carry source-specific extras that don't fit the core model yet — deadlines, documents,
   benefits — in a `raw_extras` dict for Step 3 / detail enrichment.

### 1.3 Karnataka SSP connector (`ingestion/sources/karnataka_ssp/`)

This portal is login-gated and hostile to scraping, so we keep it **read-only on public pages**.

1. **Playwright, headless:** load the public landing pages (`/`, `/ssppre/PreHome`, `/ssppre/PostHome`)
   once per run. These render **scheme lists and notice/announcement blocks** (opening dates,
   deadline extensions).
2. **Extract two things:**
   - **Scheme cards/links** → parse name, department, link, and push them into the same raw-record
     shape (normalizer will map dept → ministry, etc.).
   - **Notices** (deadline changes, new announcements) → these are the "near-real-time" signals that
     matter most. Store them as lightweight `notice` records with `published_at` and raw text.
3. **Hard rules:** never attempt login, never answer captchas, never hammer the site. One run per
   few hours max, with delays between page loads. If a page blocks us, log it and degrade to the
   last successful snapshot rather than retrying aggressively.
4. **Secondary KA sources (cheap wins):** the departmental portals already used as sources in our
   seed data (`sw.karnataka.gov.in`, `dce.karnataka.gov.in`, `sjd.karnataka.gov.in`) also publish
   scheme/notification pages and are plain HTML — a `requests + BeautifulSoup` connector there is
   simple and stable.

### 1.4 Output contract

Every connector writes:
```
data/raw/{source}/{timestamp}/schemes.json     # raw scheme records
data/raw/{source}/{timestamp}/notices.json     # notices/announcements (SSP)
```
Plus a tiny `manifest.json` (source, fetched_at, record count, status). Raw data is immutable
(never overwrite a previous timestamp dir) — that gives us an audit trail and makes re-parsing cheap.

**Acceptance criteria for Step 1:**
- Both connectors run standalone and dump raw JSON for at least one real scheme each.
- MyScheme parser output passes through `SchemeNormalizer` + `SchemeValidator` without error.
- `python ingestion/pipelines/karnataka_pipeline.py` still works unchanged (no regressions).

---

## Step 2 — Change detection + scheduled sync

### 2.1 New tables (alembic migration — one new revision)

```sql
-- What a scheme looked like last time we fetched it
CREATE TABLE scheme_snapshots (
    scheme_id   UUID PRIMARY KEY REFERENCES schemes(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,             -- sha256 of normalized content fields
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- One row per detected change (the "what's new" feed)
CREATE TABLE scheme_updates (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id     UUID REFERENCES schemes(id) ON DELETE CASCADE,
    change_type   VARCHAR(20) NOT NULL,    -- NEW | UPDATED | CLOSED
    changed_fields JSONB,                  -- {"deadline": "old" -> "new"} etc.
    detected_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_scheme_updates_detected ON scheme_updates(detected_at DESC);
CREATE INDEX idx_scheme_updates_scheme   ON scheme_updates(scheme_id);
```

### 2.2 Fingerprinting

`sync/fingerprint.py`: `sha256` over the *semantic* fields of the normalized record
(name, description, eligibility_text, category, ministry, link, tags — **excluding**
`ingested_at`/timestamps so re-fetches don't cause false positives).

### 2.3 Sync algorithm (`sync/change_detector.py` + `pipelines/live_sync_pipeline.py`)

For each run, for every fetched scheme:

```
fingerprint = sha256(normalized content fields)

snapshot = SELECT fingerprint FROM scheme_snapshots WHERE scheme_id = <id>

if snapshot is None:
    → NEW        (insert scheme, insert snapshot, emit scheme_updates row)
elif snapshot.fingerprint == fingerprint:
    → UNCHANGED  (skip; still refresh fetched_at)
else:
    → UPDATED    (upsert scheme, update snapshot, emit scheme_updates row
                  with changed_fields diff)
```

For schemes in our DB **not seen in the portal this run**:
- If missing 2 consecutive runs → mark `status = 'INACTIVE'`, emit `CLOSED`.
- One miss is tolerated (portals have flaky pages — avoid false "closed" alarms).

The pipeline **reuses the existing stages verbatim**:
`SchemeNormalizer → SchemeValidator → DedupEngine → PostgresLoader.load()`
and adds the snapshot/diff bookkeeping around them. `PostgresLoader` already handles
insert-vs-update correctly via `ON CONFLICT`.

### 2.4 Scheduler (`sync/scheduler.py`)

`APScheduler` `BackgroundScheduler`, running inside the API process (or as a standalone
`ingestion/sync/worker.py` service later):

| Source | Cadence | Rationale |
|---|---|---|
| MyScheme | every 6–12 h | catalog data, changes weekly at most |
| Karnataka SSP notices | every 2–4 h (academic season), 12 h off-season | deadlines are time-critical |
| Dept portals (KA) | every 12 h | cheap, plain HTML |

All intervals configurable via `.env` (`MYSCHEME_POLL_INTERVAL_MIN`, etc.) and disabled by
default in dev (opt-in with `LIVE_SYNC_ENABLED=true`).

### 2.5 Logging & observability

Each run writes a JSON run-report (fetched, parsed, new, updated, unchanged, closed, errors) to
`data/sync_logs/`. This is what an admin dashboard shows later, and it's our debugging breadcrumb
when a portal changes its layout.

**Acceptance criteria for Step 2:**
- Two synthetic runs with a deliberately edited record produce exactly one `UPDATED` event with the
  right `changed_fields`.
- A record removed twice in a row produces one `CLOSED` event and `status='INACTIVE'`.
- Re-running with no portal changes produces zero new `scheme_updates` rows (idempotency proven).

---

## Step 3 — Surface the updates

### 3.1 API (`services/api/routes/updates.py` — new router, mounted in `app.py`)

```
GET /api/v1/updates?change_type=NEW|UPDATED|CLOSED&since=<iso>&limit=50
  → { updates: [ { scheme: {...}, change_type, changed_fields, detected_at } ], total }
```

Reuses the existing `SchemeResponse` model. Also extend `GET /api/v1/schemes/{id}` to include
`last_updated` and `latest_update` (already partially supported — `last_updated` column exists).

### 3.2 Frontend

- **Home page:** a "Recently updated schemes" strip fed by `/api/v1/updates` (NEW badge on new
  schemes, "Updated 2h ago" chips).
- **Schemes page:** sort/filter by "Recently updated"; `NEW` badge on scheme cards (new `badge`
  field in `SchemeCard.jsx`).
- **Scheme detail:** a "What changed" panel showing `changed_fields` from the last `UPDATED` event.
- New API helpers in `frontend/src/api/api.js` mirroring the existing `getSchemes` pattern.

### 3.3 Notifications (deferred, natural next phase)

`scheme_updates` rows are the event source for a later Notification Service (email/WhatsApp/
in-app) per `docs/modules.md` §2.7 — no extra schema needed, the feed is already built.

**Acceptance criteria for Step 3:**
- After a seeded `scheme_updates` row, `/api/v1/updates` returns it with the scheme payload.
- Frontend shows the NEW/UPDATED badge and "What changed" panel with real data.
- `npm run build` + backend import check pass.

---

## Validation plan (per step)

| Step | Check |
|---|---|
| 1 | Run connectors manually; assert parsed records validate against `SchemeValidator` |
| 2 | Synthetic two-run test (edited + removed records) → assert correct events & idempotency |
| 3 | `curl /api/v1/updates`; `npm run build`; browser check of badges |

---

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| MyScheme internal API changes | Capture endpoints via DevTools as part of the build; parser isolated behind `parser.py` so only one file changes |
| SSP blocks headless browser / rate-limits | Public pages only, polite delays, degrade to last snapshot, never attempt login |
| False "closed" alarms on flaky pages | 2-consecutive-miss rule before `CLOSED` |
| Portal layout changes break parsing | Per-source parsers isolated; raw JSON preserved so re-parsing is a re-run, not a re-fetch |
| Near-real-time ≠ instant | Set expectations: this is polling-based (hours), which is correct for this domain |

---

## Decision checkpoint (before we start building)

1. **Scope:** Start with MyScheme only (richest source), then add SSP notices? Or both in parallel?
2. **Where the scheduler runs:** inside the FastAPI process (simplest) vs a separate worker container?
3. **Capture MyScheme's real API:** want me to run a browser session now to record the exact
   endpoints so Step 1 has a concrete contract?

If the approach looks right, we start with Step 1. If something feels off, we refine this document
until it feels like the one true path — that's the point of having it written down.
