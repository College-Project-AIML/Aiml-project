# understand.md — Project File Guide

Every file in the Aiml-project, what it does, and why it exists.

---

## Root Files

### `README.md`
Project overview document. Describes the vision, philosophy, tech stack, privacy model, and development strategy. Written as a portfolio/learning project README — not a usage guide.

### `docker-compose.yml`
Defines the local development infrastructure. Runs a single **PostgreSQL 15** container (`aiml_postgres`) on port **5433**. Auto-initializes the database by mounting `schemas/postgres.sql` into the container's init directory. No other services — no Redis, no MongoDB, no Kafka. Just Postgres.

### `requirements.txt`
Python dependencies for the entire backend:
- `psycopg2-binary` — PostgreSQL driver
- `python-dotenv` — Loads `.env` files into environment variables
- `fastapi` — Web framework for the API
- `uvicorn` — ASGI server to run FastAPI
- `pydantic` — Data validation (used by FastAPI models)
- `beautifulsoup4` / `html2text` — HTML parsing for ingestion scrapers

### `.env.example`
Template for environment variables. Contains PostgreSQL connection defaults (user: `admin`, password: `securepassword`, db: `aiml_core`, port: `5433`) and the full `DATABASE_URL` string. Copy this to `.env` before running anything.

### `.gitignore`
Excludes `node_modules/`, `venv/`, `__pycache__/`, `.env` files, `data/` directory, `logs/`, build outputs (`dist/`, `build/`), and IDE configs from version control.

### `scholarships_api_dump.json`
Raw data dump of **885 scholarship records** scraped from `scholarships.gov.in`. This is the primary real-world data source. The Karnataka pipeline can ingest this file, or fall back to its own sample data if the file is missing.

---

## `schemas/`

### `schemas/postgres.sql`
The complete PostgreSQL database schema. Creates 6 tables:

| Table | Purpose |
|---|---|
| `providers` | Government ministries/departments that run schemes |
| `categories` | Scheme types (Scholarship, Welfare, Subsidy, etc.) |
| `schemes` | Main table — scheme name, description, eligibility text, state, status, tags, confidence score, source URL |
| `eligibility_rules` | Structured criteria per scheme — age range, income cap, gender, caste, states, education level |
| `benefits` | What each scheme provides — type, amount, frequency |
| `documents_required` | Documents needed to apply — name and whether mandatory |

Uses UUID primary keys (`uuid-ossp` extension), `TIMESTAMP WITH TIME ZONE`, `ON DELETE CASCADE` foreign keys, and a **GIN full-text search index** on scheme name + description. No ENUMs — all VARCHAR for flexibility.

---

## `scripts/`

### `scripts/seed_schemes.py`
Populates the database with realistic Indian government scheme data. Run this after starting PostgreSQL to get a working dataset.

What it seeds:
- **6 providers** (Ministry of Education, Social Justice, Science & Tech, Karnataka state, Tribal Affairs, Minority Affairs)
- **8 categories** (Scholarship, Fellowship, Grant, Loan, Subsidy, Skill Program, Training Program, Welfare Scheme)
- **25 schemes** with full detail — each gets an eligibility rule, 1-3 benefits, and 2-5 required documents

How it works:
1. Reads and executes `schemas/postgres.sql` to ensure tables exist
2. Inserts providers, categories, then schemes with all child records
3. Uses deterministic UUIDs (`uuid5`) so it's idempotent — safe to re-run
4. Uses `ON CONFLICT DO NOTHING` on all inserts
5. Prints a summary table with row counts

Connection: reads `DATABASE_URL` env var first, falls back to individual `POSTGRES_*` vars, or hard-coded defaults.

### `scripts/setup.sh`
Quick bootstrap script. Copies `.env.example` to `.env` if it doesn't exist, creates local data directories, and runs `docker-compose up -d`. Prints connection info when done.

---

## `ingestion/` — Data Pipeline

The ingestion system takes raw government scheme data and processes it through: **normalize → validate → deduplicate → save**.

### `ingestion/__init__.py`
Empty. Makes `ingestion` a Python package so imports work.

### `ingestion/models/scheme_model.py`
Defines `SchemeModel` — a Python dataclass that is the canonical data structure for all schemes. Fields include identity (`scheme_id`, `name`, `source`), classification (`category`, `ministry`, `state_code`), content (`description`, `eligibility_text`, `link`), intelligence support (`tags`, `confidence_score`), governance metadata (`ingested_at`, `source_type`, `data_lineage`), and AI placeholders (`embedding_id`, `vector_status`). Acts as the contract between all layers.

### `ingestion/normalizers/scheme_normalizer.py`
`SchemeNormalizer` class. Converts raw scraped/parsed records into the structured system format. Specifically:
- Generates deterministic `scheme_id` from a SHA-256 hash of name + source + state
- Maps raw category strings to controlled vocabulary (`"scholarship"` → `"SCHOLARSHIP"`, `"welfare"` → `"WELFARE_SCHEME"`)
- Normalizes state codes (`"karnataka"` → `"KA"`)
- Cleans whitespace, normalizes ministry names
- Auto-generates tags by tokenizing name + description + eligibility text
- Assigns confidence scores based on source (`.gov.in` → 0.95, unknown → 0.6)

### `ingestion/validators/scheme_validator.py`
`SchemeValidator` class. Governance gate that ensures data quality before storage. Checks:
- **Required fields** — scheme_id, source, name, category, ministry, description, state_code, confidence_score, status, version
- **Type correctness** — strings are strings, scores are numeric, tags are lists
- **Category validity** — must be in the allowed set (SCHOLARSHIP, FELLOWSHIP, GRANT, etc.)
- **Status validity** — must be ACTIVE, INACTIVE, or DEPRECATED
- **Privacy protection** — scans all string values for banned words (aadhaar, pan, bank, biometric, passport, etc.) and rejects records containing them
- **Confidence score range** — must be 0–1
- **State code format** — 2-3 characters
- **Link format** — must start with `http`

Raises `ValidationError` on any failure.

### `ingestion/dedup/dedup_engine.py`
`DedupEngine` class. Removes duplicate records in two phases:
1. **Exact dedup** — removes records with identical `scheme_id` values (O(n) hash-based)
2. **Fuzzy dedup** — compares scheme names using `difflib.SequenceMatcher`. If two names have ≥85% similarity (configurable threshold), the second one is dropped

Tracks statistics: total_in, exact_duplicates, near_duplicates, total_out. Has a `report()` method for human-readable output.

### `ingestion/loaders/json_loader.py`
`JsonLoader` class. File-based persistence for pipeline outputs.
- `save(records, path)` — creates directories, wraps records in a metadata envelope (`total_records`, `exported_at`, `format_version`), writes pretty-printed JSON
- `load(path)` — reads JSON, handles both wrapped format `{"metadata":..., "records":[...]}` and raw lists

### `ingestion/loaders/postgres_loader.py`
`PostgresLoader` class. Bulk upserts scheme records into the PostgreSQL `schemes` table.
- Uses `INSERT ... ON CONFLICT (id) DO UPDATE` for idempotent loads
- Auto-creates categories in the `categories` table via `_ensure_category()` with an in-memory cache
- Generates deterministic UUIDs from scheme_id hashes using SHA-256
- Tracks stats: inserted, updated, failed, categories_created
- Connects using `DATABASE_URL` from environment

### `ingestion/pipelines/govt_pipeline.py`
`GovtIngestionPipeline` — the original pipeline controller. Orchestrates ingestion from central (scholarships.gov.in) and state (Karnataka PDF) sources. Calls normalize → validate → store for each record. Logs failures with full context. Has a stats report. This is the **original** pipeline that uses the `StorageAdapter`.

### `ingestion/pipelines/karnataka_pipeline.py`
`KarnatakaPipeline` — the **new** production-style pipeline specifically for Karnataka data. This is the main pipeline to use.

Orchestration flow:
1. **Load raw data** — from constructor arg, `scholarships_api_dump.json`, or 20 built-in sample Karnataka schemes
2. **Normalize** — via `SchemeNormalizer`
3. **Validate** — via `SchemeValidator` (collects errors, doesn't crash)
4. **Deduplicate** — via `DedupEngine`
5. **Save to JSON** — via `JsonLoader` → `data/gov/karnataka/schemes.json`
6. **Save to PostgreSQL** — via `PostgresLoader` (skippable with `--skip-postgres`)

The 20 built-in sample schemes cover Karnataka-specific programs: Vidyasiri SC/ST scholarship, Arivu minority loan, Bhagyalakshmi girl child welfare, Krishi Yantra farm equipment subsidy, Arogya Sanjeevini health insurance, Sanchi Honnamma girls scholarship, and more.

CLI usage: `python -m ingestion.pipelines.karnataka_pipeline [--skip-postgres] [--input path/to/file.json]`

### `ingestion/storage/storage_adapter.py`
`StorageAdapter` — the original simple storage layer. Creates a basic `schemes` table on init and provides a `save(scheme)` method using `INSERT ... ON CONFLICT DO NOTHING`. This is used by the original `govt_pipeline.py`. The newer `postgres_loader.py` is more feature-rich and used by `karnataka_pipeline.py`.

### `ingestion/sources/central/scholarships_gov_in.py`
Scraper for the central `scholarships.gov.in` portal. Contains a `scrape()` function. Fetches scholarship listing pages, parses HTML with BeautifulSoup, extracts scheme records. Used by `govt_pipeline.py`.

### `ingestion/sources/central/__init__.py`
Empty. Makes `central` a Python package.

### `ingestion/sources/karnataka/scholarship_pdf_ingestor.py`
PDF parser for Karnataka scholarship documents. Contains a `parse_pdf()` function. Reads `tmp/karnataka_scholarships.pdf`, extracts text line-by-line, and structures it into scheme records. Used by `govt_pipeline.py`.

### `ingestion/sources/karnataka/__init__.py`
Empty. Makes `karnataka` a Python package.

### Other `__init__.py` files
`ingestion/models/__init__.py`, `ingestion/normalizers/__init__.py`, `ingestion/validators/__init__.py`, `ingestion/storage/__init__.py`, `ingestion/pipelines/__init__.py`, `ingestion/dedup/__init__.py`, `ingestion/loaders/__init__.py`, `ingestion/sources/__init__.py` — all empty, just make their directories importable as Python packages.

---

## `services/api/` — FastAPI Backend

The REST API that serves data from PostgreSQL to the frontend.

### `services/api/app.py`
Main FastAPI application entry point. Sets up:
- **Lifespan events** — initializes DB connection pool on startup, closes it on shutdown
- **CORS middleware** — allows all origins (development mode)
- **4 routers** mounted under `/api/v1` prefix: schemes, search, categories, eligibility
- **Health check** at `/health`
- **Root info** at `/`

Run with: `uvicorn services.api.app:app --reload --port 8000`
Swagger docs at: `http://localhost:8000/docs`

### `services/api/db.py`
Database connection module. Uses `psycopg2.pool.SimpleConnectionPool` (1–10 connections). Provides:
- `init_pool()` / `close_pool()` — lifecycle management
- `get_db()` — context manager that checks out a connection, creates a `RealDictCursor`, auto-commits on success, rolls back on error, and returns the connection to the pool

Loads `DATABASE_URL` from environment with fallback to localhost defaults.

### `services/api/models/scheme.py`
Pydantic models for request/response validation:
- `SchemeResponse` — standard scheme fields (id, name, description, eligibility_text, state_code, status, tags, etc.)
- `SchemeDetailResponse` — extends SchemeResponse with eligibility_rules, benefits, and documents_required lists
- `SchemeListResponse` — paginated list wrapper (schemes, total, page, limit)
- `CategoryResponse` — category with scheme_count
- `EligibilityCheckRequest` — user profile input (age, income, gender, caste, state, education_level)
- `EligibilityCheckResponse` / `EligibilityMatchResponse` — matching results with reasons
- `SearchResponse` — search results wrapper
- `EligibilityRuleResponse`, `BenefitResponse`, `DocumentRequiredResponse` — sub-models

### `services/api/routes/schemes.py`
Two endpoints:

**`GET /api/v1/schemes`** — Paginated scheme list
- Query params: `page`, `limit`, `category`, `state`, `status` (default: ACTIVE)
- Joins with categories and providers for names
- Orders by confidence_score DESC, then name
- Returns `{schemes, total, page, limit}`

**`GET /api/v1/schemes/{scheme_id}`** — Full scheme detail
- Returns scheme with all eligibility rules, benefits, and required documents
- 404 if not found

### `services/api/routes/search.py`
**`GET /api/v1/search?q=`** — Full-text search
- Primary: PostgreSQL `to_tsvector`/`plainto_tsquery` with `ts_rank` ordering
- Fallback: if FTS returns nothing, falls back to `ILIKE` pattern matching on name and description
- Returns up to 50 results

### `services/api/routes/categories.py`
**`GET /api/v1/categories`** — All categories with scheme counts
- LEFT JOINs categories with schemes, groups and counts
- Orders by scheme_count DESC

### `services/api/routes/eligibility.py`
**`POST /api/v1/eligibility-check`** — Eligibility matching
- Accepts a user profile (age, income, gender, caste, state, education_level)
- Builds dynamic SQL conditions that match against `eligibility_rules` table
- NULL rule fields are treated as "no restriction" (open to all)
- Returns matching schemes with human-readable match_reason strings
- Limited to 50 results, ordered by confidence_score

### `services/__init__.py`, `services/api/__init__.py`, `services/api/models/__init__.py`, `services/api/routes/__init__.py`
Empty. Make directories importable as Python packages.

---

## `frontend/` — React + Vite Frontend

Single-page application for browsing government schemes.

### `frontend/package.json`
Node.js project configuration. Dependencies:
- `react` + `react-dom` — UI framework
- `react-router-dom` — Client-side routing
- `axios` — HTTP client for API calls
- `vite` + `@vitejs/plugin-react` — Build tool and React plugin

Scripts: `dev` (development server), `build` (production build), `preview` (preview production build).

### `frontend/vite.config.js`
Vite configuration. Runs dev server on **port 3000**. Proxies `/api` requests to `http://localhost:8000` (the FastAPI backend) so the frontend doesn't need to worry about CORS during development.

### `frontend/index.html`
Root HTML file — Vite's entry point. Loads the Inter font from Google Fonts and mounts the React app at `<div id="root">`.

### `frontend/src/main.jsx`
React entry point. Renders the `<App>` component wrapped in `<BrowserRouter>` and `<React.StrictMode>`. Imports global CSS.

### `frontend/src/App.jsx`
Main application component. Defines:
- **Navigation bar** — sticky top nav with links to Home, Schemes, and Eligibility. Active link highlighting based on current route.
- **Routes** — `/` (Home), `/schemes` (Schemes list), `/schemes/:id` (Scheme detail), `/eligibility` (Eligibility checker)
- **Footer** — simple project attribution

### `frontend/src/App.css`
Global stylesheet. Defines:
- CSS custom properties (design tokens) — colors (government blue/teal palette), shadows, border radius, typography
- Base styles — Inter font, antialiasing, link transitions
- Navigation — dark blue sticky navbar with hover/active states
- Page layout — min-height, header gradients
- Card styles — white backgrounds, borders, hover shadows
- Button styles — primary (blue), accent (teal), outline variants
- Tag/badge styles — colored pills for categories and status
- Form styles — inputs with focus rings
- Loading spinner animation
- Empty state styling
- Footer styling

### `frontend/src/api/api.js`
API client layer. Creates an Axios instance with base URL `/api/v1` and 10-second timeout. Exports 5 functions:
- `getSchemes({ page, limit, category, state, status })` — fetches paginated scheme list
- `getScheme(id)` — fetches single scheme detail
- `searchSchemes(query)` — full-text search
- `getCategories()` — fetches all categories
- `checkEligibility(profile)` — posts user profile, gets matching schemes

### `frontend/src/pages/Home.jsx`
Landing page. Features:
- **Hero section** — gradient background with headline, subtext, and a search bar
- **Category grid** — loads categories from API, displays as clickable cards with scheme counts and emoji icons
- **Featured schemes** — shows top 6 schemes ordered by confidence score, each as a SchemeCard
- **Call-to-action** — "Check Eligibility" banner at the bottom

### `frontend/src/pages/Schemes.jsx`
Scheme browsing page. Features:
- **Search bar** at the top — triggers API search, clears with an X button
- **Category filter chips** — loaded from API, click to filter by category
- **Scheme list** — paginated grid of SchemeCards
- **Pagination** — Previous/Next buttons with page indicator
- **Loading and empty states**

### `frontend/src/pages/SchemeDetail.jsx`
Individual scheme detail page. Shows:
- **Scheme header** — name, provider, category badge, status badge, confidence score bar
- **Description section** — full text description
- **Eligibility section** — text eligibility + structured rules (age range, income cap, gender, caste, states, education)
- **Benefits section** — cards for each benefit showing type, amount, and frequency
- **Required documents** — list with mandatory/optional badges
- **Source link** — external link to official source
- **Back button** — returns to schemes list

### `frontend/src/pages/Eligibility.jsx`
Eligibility checker page. Features:
- **Profile form** — fields for age, annual income, gender (dropdown), caste category (dropdown), state (dropdown), and education level (dropdown)
- **Submit button** — posts profile to eligibility-check API
- **Results section** — shows matching schemes as SchemeCards with match_reason displayed
- **Loading state** during API call
- **Empty state** when no matches found

### `frontend/src/components/SchemeCard.jsx`
Reusable card component for displaying a scheme in a list. Shows:
- Category name (as a tag)
- Scheme name (linked to detail page)
- Truncated description (150 chars)
- State code badge
- Confidence score as a visual progress bar
- Up to 3 tags

### `frontend/src/components/SearchBar.jsx`
Reusable search input component. Props: `value`, `onChange`, `onSearch`, `placeholder`. Submits on Enter key. Has a dark variant for use on gradient backgrounds (hero section).

### `frontend/src/components/Filters.jsx`
Category filter chip component. Displays a row of clickable category buttons. Active category gets highlighted styling. "All" button to clear filter. Shows scheme_count on each chip.

---

## `docs/` — Architecture Documents

These are design/planning documents written before implementation. They describe the full vision of the system, not the current working state. Many features described here (microservices, event bus, Redis, Neo4j, Kubernetes, etc.) are **not implemented** — they represent future aspirations.

### `docs/architecture.md`
System architecture document. Describes a layered architecture with 8 layers (Frontend, API Gateway, Core Services, Data Intelligence, AI/ML, MCP Orchestration, Data, DevOps). Includes flow diagrams, privacy architecture, security architecture, event-driven design, and deployment models. The **actual implementation** is much simpler — a monolithic FastAPI backend with PostgreSQL.

### `docs/modules.md`
Modules document. Defines 14 logical modules (Auth, User Profile, Scheme Management, Eligibility Engine, Recommendation, Document Intelligence, Notification, Analytics, Data Ingestion, AI/ML, MCP Orchestration, Security, Privacy, DevOps). Each with responsibilities and sub-components. Most of these are **not yet implemented** — only the Scheme Management, Eligibility, and Data Ingestion modules have working code.

### `docs/mvp.md`
MVP definition document. Defines what the minimum viable platform should demonstrate. Lists core features for users, schemes, eligibility, recommendations, data ingestion, admin, privacy, and security. The current system implements **scheme browsing, search, eligibility checking, and data ingestion** from this list.

### `docs/roadmap.md`
9-phase roadmap from system design to scale simulation. Phases: Design → Data Layer → Backend → Ingestion → Frontend → AI → MCP → DevOps → Hardening. The project is currently in the **Phase 2–5 range** (data layer, backend, ingestion, and frontend are built).

### `docs/scope.md`
Scope document. Defines what's in-scope (scheme discovery, eligibility prediction, recommendations, ingestion, analytics) and out-of-scope (IoT, biometrics, payments, identity verification). Defines user roles (Citizen, NGO, Admin, Research, System AI). Establishes system boundaries — the platform recommends and predicts, it does NOT process applications or verify identity.

### `docs/security.md`
Security architecture document. Describes a zero-trust security model with layers from network to audit. Covers authentication (JWT), authorization (RBAC/ABAC), API security, encryption, secrets management, AI security, threat model, and incident response. The **current implementation** has none of this — no auth, no RBAC, no JWT. All endpoints are open as specified in the build requirements.

---

## `tmp/`

### `tmp/karnataka_scholarships.pdf`
A PDF document containing Karnataka state scholarship information. Used as input by the `scholarship_pdf_ingestor.py` parser. This is raw source data.

---

## How Everything Connects

```
                    scholarships_api_dump.json
                              │
                              ▼
              ┌─── Karnataka Pipeline ───┐
              │  normalize → validate    │
              │  → deduplicate → save    │
              └──────────┬───────────────┘
                    ┌────┴────┐
                    ▼         ▼
           JSON file      PostgreSQL
     (data/gov/karnataka/   (schemes, eligibility_rules,
      schemes.json)          benefits, documents_required,
                             providers, categories)
                                │
                                ▼
                         FastAPI Backend
                       (services/api/app.py)
                      /api/v1/schemes
                      /api/v1/search
                      /api/v1/categories
                      /api/v1/eligibility-check
                                │
                                ▼
                        React Frontend
                     (frontend/ on :3000)
                    proxies /api → :8000
```

**To run the full system:**
1. `docker compose up -d` — starts PostgreSQL on port 5433
2. `python scripts/seed_schemes.py` — seeds database with 25 schemes
3. `uvicorn services.api.app:app --reload --port 8000` — starts API
4. `cd frontend && npm run dev` — starts UI at localhost:3000
