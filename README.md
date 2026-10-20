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

## How to Run the Project (Step-by-Step)

You can run the project in two main ways:
- **Option 1: Local Development Mode (Recommended)** — Run the FastAPI backend and React frontend locally, connecting either to **Neon Cloud PostgreSQL (serverless)** or **Local Docker PostgreSQL**.
- **Option 2: Docker Compose (Full Stack)** — Run everything (PostgreSQL, FastAPI Backend, React Frontend) in containerized services.

---

### Prerequisites

| Tool | Version / Requirement | Notes |
| :--- | :--- | :--- |
| **Python** | `3.10` – `3.13` | *Python 3.14+ has breaking C-API changes for PyO3 wheels.* |
| **Node.js & npm** | `v18.0.0+` & `npm 9+` | For React Vite frontend |
| **Git** | Any modern version | Source control |
| **Docker** *(Optional)* | Docker Desktop | Only required if running PostgreSQL locally or full-stack containers |
| **Neon CLI** *(Optional)* | Installed via `npm i -g neon` | If using Neon Cloud Postgres branch management |

---

### Database Setup: Choose Option A or B

#### Option A: Neon Cloud PostgreSQL (Serverless — No Docker required)
The project is configured to work out-of-the-box with **Neon Serverless Postgres**:
- Project: `aiml-schemes` (`jolly-resonance-61500227`)
- Branch: `production` (`br-empty-moon-b46kpd2l`)

Your `.env` file receives the cloud `DATABASE_URL` directly:
```env
DATABASE_URL=postgresql://neondb_owner:npg_WmHT3hrlks1p@ep-aged-term-b4z9d879-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

#### Option B: Local PostgreSQL (via Docker)
If you prefer running a local database instead of cloud Neon:
- Run: `docker compose up -d postgres`
- Database runs on: `localhost:5433`, User: `admin`, Password: `securepassword`, Database: `aiml_core`
- Point `.env` to: `DATABASE_URL=postgresql://admin:securepassword@localhost:5433/aiml_core`

---

### Option 1: Local Development Guide

#### 🍎 macOS & Linux Instructions

##### 1. Setup Environment Configuration
```bash
# In the project root directory
cp .env.example .env
```
*(If using Neon Cloud, ensure your `.env` contains the Neon `DATABASE_URL`, or run `neon link -y`)*

##### 2. Start Database (Skip if using Neon Cloud)
```bash
docker compose up -d postgres
```

##### 3. Create Python Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip & install backend packages
pip install --upgrade pip
pip install -r requirements.txt
```

##### 4. Initialize Database Schema & Seed Data
```bash
# Ensure venv is active: source venv/bin/activate

# 1. Apply user events migration
psql "$DATABASE_URL" -f services/api/migrations/001_user_events.sql
# (Or if using local docker: docker exec -i aiml_postgres psql -U admin -d aiml_core < services/api/migrations/001_user_events.sql)

# 2. Stamp Alembic migration baseline
alembic stamp head

# 3. Seed initial 25+ government schemes with eligibility rules & benefits
python -m scripts.seed_schemes
```

##### 5. Start the FastAPI Backend Server
```bash
# Ensure venv is active: source venv/bin/activate
uvicorn services.api.app:app --reload --port 8000
```
- API Root: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

##### 6. Start the React Frontend Development Server (Open a New Terminal Window)
```bash
# Navigate to frontend directory
cd frontend

# Install Node modules
npm install

# Start Vite dev server
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

#### 🪟 Windows Instructions

##### 1. Setup Environment Configuration

**PowerShell:**
```powershell
Copy-Item .env.example .env
```

**Command Prompt (cmd):**
```cmd
copy .env.example .env
```
*(If using Neon Cloud, ensure your `.env` contains the Neon `DATABASE_URL`, or run `neon link -y`)*

##### 2. Start Database (Skip if using Neon Cloud)
```cmd
docker compose up -d postgres
```

##### 3. Create Python Virtual Environment & Install Dependencies

**PowerShell:**
```powershell
# Create virtual environment
python -m venv venv

# If execution policy blocks scripts, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip & install backend packages
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Command Prompt (cmd):**
```cmd
:: Create virtual environment
python -m venv venv

:: Activate virtual environment
venv\Scripts\activate.bat

:: Upgrade pip & install backend packages
python -m pip install --upgrade pip
pip install -r requirements.txt
```

##### 4. Initialize Database Schema & Seed Data
```cmd
:: Ensure virtual environment is activated

:: 1. Stamp Alembic migration baseline
alembic stamp head

:: 2. Seed initial 25+ government schemes with eligibility rules & benefits
python -m scripts.seed_schemes
```

##### 5. Start the FastAPI Backend Server
```cmd
:: Ensure virtual environment is activated
python -m uvicorn services.api.app:app --reload --port 8000
```
- API Root: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

##### 6. Start the React Frontend Development Server (Open a New Terminal / Command Prompt)
```cmd
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

### Option 2: Docker Compose (Full Stack — Containerized)

To build and spin up the complete architecture (PostgreSQL, FastAPI Backend, and React Frontend) with a single command:

#### macOS / Linux:
```bash
cp .env.example .env
docker compose up --build -d
```

#### Windows:
```cmd
copy .env.example .env
docker compose up --build -d
```

#### Services Port Mapping:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database**: `localhost:5433` (Database: `aiml_core`, User: `admin`)

#### Stopping Containers:
```bash
docker compose down
```

---

### Advanced / Pipeline Commands

#### Run Near-Real-Time Scheme Sync Pipeline Manually
Polls official government portals (MyScheme & Karnataka SSP), fingerprints changes, and writes updates to the database:

**macOS / Linux:**
```bash
source venv/bin/activate
python -m ingestion.pipelines.live_sync_pipeline
```

**Windows:**
```cmd
venv\Scripts\activate
python -m ingestion.pipelines.live_sync_pipeline
```

#### Train the Real ML Ranking Model
Trains the LightGBM / XGBoost interaction ranking model using recorded user telemetry and profile snapshots:

**macOS / Linux:**
```bash
source venv/bin/activate
python -m services.api.ml.train_real
```

**Windows:**
```cmd
venv\Scripts\activate
python -m services.api.ml.train_real
```

---

### Summary of Service Ports

| Service | Local Dev URL / Port | Docker Compose URL / Port |
| :--- | :--- | :--- |
| **Frontend UI** | `http://localhost:5173` | `http://localhost:3000` |
| **Backend API** | `http://localhost:8000` | `http://localhost:8000` |
| **Swagger Docs** | `http://localhost:8000/docs` | `http://localhost:8000/docs` |
| **Local PostgreSQL** | `localhost:5433` | `localhost:5433` |
| **Neon PostgreSQL** | Cloud Endpoint (`5432`) | Cloud Endpoint (`5432`) |

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
