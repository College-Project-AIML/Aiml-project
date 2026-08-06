# Aiml-project

**Cloud-native • AI-assisted • System-first • Student-scale • Architecture-driven**

---

## Overview

Aiml-project is a **student-built, cloud-native, AI-assisted digital public utility system prototype** designed to help users discover, understand, and access **government schemes, scholarships, welfare programs, and social initiatives** in a structured, intelligent, and privacy-first way.

It is built as a **real system**, not a demo app — focused on:

- system architecture
- data engineering
- AI integration
- cloud engineering
- privacy-first design
- governance and scale thinking

This project is a **learning + portfolio + research-grade prototype**, not a commercial product.

---

## Core Problem

Government and social welfare programs are:

- fragmented
- unstructured
- hard to navigate
- complex to understand
- inaccessible to common users

There is no unified system that provides:

- structured discovery
- eligibility understanding
- intelligent filtering
- personalized recommendations
- explainable logic

Aiml-project solves this using **structured data models, rule engines, AI support layers, and clean system architecture**.

---

## System Philosophy

**System-first engineering principles:**

- Architecture before implementation
- Data before intelligence
- Logic before AI
- System before UI
- Structure before automation
- Governance before scale
- Privacy before convenience
- Engineering before aesthetics

This is **not feature-first development**.

---

## Tech Stack

### Cloud & Infrastructure

- Cloud Provider: Azure
- Containers: Docker
- Orchestration: Kubernetes (AKS – student scale)
- Secrets: Azure Key Vault
- CI/CD: GitHub Actions

### Frontend

- React
- Node.js toolchain

### Backend

- Node.js microservices
- API Gateway architecture

### AI Layer

- Python services
- ML pipelines
- NLP processing
- Vector embeddings

### Data Layer

- PostgreSQL – core structured data
- Redis – cache/session
- Graph DB – relationship modeling
- Vector DB – AI embeddings
- Azure Storage – files/blobs

---

## Functional Layers

### Scheme & Program Discovery

- Browse schemes
- Search & filter
- Category exploration
- Structured navigation

### Eligibility System

- Rule-based eligibility engine
- Condition matching
- Profile abstraction
- Explainable scoring

### Recommendation System

- Ranking engine
- Priority scoring
- Similarity matching
- Context-aware suggestions

### AI Support Layer

AI is used for:

- classification
- tagging
- similarity scoring
- semantic search
- ranking support
- NLP parsing

AI does NOT:

- approve eligibility
- make legal decisions
- replace logic
- override rules

---

## Privacy & Ethics

Privacy-first by design.

The system never stores:

- Aadhaar
- PAN
- bank details
- biometrics
- documents
- identity proofs
- exact addresses

Only abstracted data:

- age group
- income bracket
- category
- district/state
- occupation group

Principles:

- data minimization
- consent-based processing
- anonymization
- abstraction
- no surveillance
- no profiling abuse

---

## Data Strategy

### Government Data (Primary)

- State-first approach (Karnataka seed dataset)
- Structured manual seeding
- Schema-first design
- Semi-automation → automation

### Private Data (Secondary)

- Manual curation
- Reference-based data
- Official source linking
- Compliance-safe ingestion
- No content mirroring

---

## Architecture Model

Layered system design:

- Frontend Layer
- API Gateway
- Service Layer
- Logic Layer
- Data Layer
- AI Layer
- Ingestion Layer
- Orchestration Layer (MCP)
- Security Layer
- Storage Layer
- DevOps Layer

Modular • Governed • Expandable • Clean

---

## Development Model

Build order:

1. Foundation lock
2. Architecture design
3. Data modeling
4. System logic
5. Backend services
6. Eligibility engine
7. Recommendation system
8. Admin system
9. Ingestion pipelines
10. AI layer
11. MCP orchestration
12. Frontend
13. DevOps
14. Hardening & scale prep

**Architecture → Data → System → AI → Scale**

---

## Project Nature

This project is:

- student-built
- portfolio-grade
- research-grade
- learning-focused
- architecture-driven
- system-engineering focused

This project is NOT:

- a startup
- a SaaS product
- a commercial platform
- a government system
- a monetized service

---

## Scope Discipline

### Focus on:

- architecture
- system design
- data engineering
- AI integration
- cloud engineering
- privacy
- governance

### Avoid:

- feature bloat
- buzzwords
- overengineering
- fake scalability
- tool addiction
- enterprise cosplay
- startup theatrics

---

## Project Vision Statement

> Aiml-project is a cloud-native, AI-assisted, privacy-first, student-built digital public utility system prototype designed to demonstrate real-world system architecture, data engineering, AI integration, and cloud engineering with controlled scope, ethical design, and engineering discipline.

---

## How to Use This Repository

This repository is designed for:

- learning system design
- studying architecture
- understanding AI integration
- building cloud-native systems
- practicing data engineering
- portfolio demonstration

---

## Near-Real-Time Scheme Updates (docs/next.md)

The project includes a live-sync engine that polls government portals, detects
changes, and surfaces them to users:

- **Connectors** — `ingestion/sources/myscheme/` (configurable internal JSON API,
  endpoint set via `MYSCHEME_API_URL`) and `ingestion/sources/karnataka_ssp/`
  (public landing pages only, read-only & polite).
- **Sync engine** — `ingestion/sync/` (fingerprinting, change detection, APScheduler)
  orchestrated by `ingestion/pipelines/live_sync_pipeline.py`.
- **Tables** — `scheme_snapshots` and `scheme_updates` (alembic revision
  `b2a9f3c1d4e7`).
- **API & UI** — `GET /api/v1/updates`, a “Recently updated” sort, NEW/UPDATED
  badges, and a “What changed” panel on scheme detail.

Run one sync pass manually:

```bash
venv/bin/python -m ingestion.pipelines.live_sync_pipeline
```

Scheduled runs are opt-in via `LIVE_SYNC_ENABLED=true` (see `.env.example`).

> **Note on migrations:** a fresh DB built from `schemas/postgres.sql` already
> contains the new tables (the file is mounted as the docker init script), so run
> `venv/bin/alembic stamp head` after the initial `docker compose up`; use
> `venv/bin/alembic upgrade head` on an existing DB that predates them.

---

## License & Usage

This project is for **educational and research purposes only**.

Not intended for commercial deployment.
Not intended for production use.
Not affiliated with any government or private entity.

---

## Master Instruction

When working on this project:

> Build systems, not apps.
> Build structure, not chaos.
> Build architecture, not hacks.
> Build intelligence, not hype.
> Build responsibly, not recklessly.

---

**Aiml-project — System-first. Data-first. Intelligence-driven. Privacy-first.**
