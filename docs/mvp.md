# Aiml-project — MVP Definition Document

## 1. MVP Philosophy

The MVP (Minimum Viable Platform) of Aiml-project is not a minimal UI demo — it is a **minimal functioning system architecture** that proves:

- Core data flows
- Core logic flows
- Core intelligence flows
- Core privacy model
- Core modular design
- Core scalability model

The MVP is designed to validate **system architecture, not feature quantity**.

> MVP goal: Prove that the platform can ingest data, process users, match schemes, and generate intelligent outputs in a scalable, privacy-first way.

---

## 2. MVP Objectives

The MVP must demonstrate:

- Automated scheme discovery
- User profiling
- Eligibility matching
- Recommendation generation
- Data ingestion
- Modular backend architecture
- AI-readiness
- Privacy-by-design
- Security enforcement
- Scalable system structure

---

## 3. MVP Core Features

### 👤 User Features

- User registration
- Secure login
- Basic profile creation
- Profile editing
- Consent capture
- Privacy settings
- Role selection (Citizen / Admin)

---

### 📚 Scheme Features

- Scheme database
- Scheme categories
- Scheme metadata
- Search & filter
- Scheme detail view
- Rule storage
- Scheme versioning

---

### 🧮 Eligibility Features

- Rule-based eligibility checking
- Constraint matching
- Eligibility scoring (basic)
- Probability output
- Explanation output

---

### 🤖 Recommendation Features

- Basic recommendation engine
- Rule-based ranking
- Category matching
- Priority scoring
- Personalization logic (basic)

---

### 🔄 Data Ingestion Features

- Automated data ingestion
- API ingestion support
- File ingestion (CSV/PDF)
- Basic scraping
- Parsing pipeline
- Data normalization
- Auto-update scheduling

---

### 📊 Admin Features

- Admin dashboard
- Scheme management
- Data monitoring
- User analytics
- System health view
- Logs access (restricted)

---

### 🛡 Privacy Features

- Consent management
- Data minimization
- Abstraction layer
- User data control
- Data deletion
- Anonymization

---

### 🔐 Security Features

- Authentication
- Authorization
- RBAC
- Secure APIs
- Encrypted storage
- Audit logging

---

## 4. MVP Technical Stack (Minimal Mode)

### Backend:

- Node.js / FastAPI
- REST APIs
- JWT authentication
- Microservices (lightweight)

### Databases:

- PostgreSQL (core data)
- Redis (cache/sessions)
- File storage (local)

### Data:

- JSON ingestion
- CSV ingestion
- API ingestion

### AI (MVP level):

- Rule-based engine
- Simple scoring model
- No deep ML initially

### DevOps:

- Docker
- Docker Compose
- GitHub
- Local deployment
- GitHub Actions (basic CI)

### Frontend:

- Next.js
- Basic dashboards
- Role-based UI

---

## 5. MVP Architecture Scope

### Included:

- API Gateway
- Auth service
- User service
- Scheme service
- Eligibility engine
- Recommendation engine
- Ingestion pipeline
- Admin UI
- Frontend UI
- Privacy layer
- Security layer

### Excluded:

- Advanced AI models
- Deep ML training
- Cloud orchestration
- Kubernetes
- Kafka
- Airflow
- Neo4j
- Vector DB
- MCP orchestration
- Multi-region deployment
- Auto-scaling
- Disaster recovery

---

## 6. MVP Data Flow

```
User → Frontend → API Gateway → Core Services → Data Layer
                                   ↓
                            Eligibility Engine
                                   ↓
                          Recommendation Engine
                                   ↓
                              User Dashboard
```

---

## 7. MVP System Validation Criteria

The MVP is considered successful if it can:

- Store schemes
- Store users
- Match users to schemes
- Generate eligibility results
- Produce recommendations
- Ingest new schemes automatically
- Enforce privacy rules
- Enforce access control
- Demonstrate modular services
- Show scalable architecture design

---

## 8. MVP Non-Goals

The MVP will NOT:

- Replace government portals
- Process applications
- Perform identity verification
- Execute payments
- Integrate Aadhaar/PAN
- Store sensitive IDs
- Track users
- Perform surveillance
- Use biometric data
- Do behavioral profiling
- Act as an authority system

---

## 9. MVP Build Strategy

```
Schemas → Data → Backend → Ingestion → Logic → UI → Privacy → Security → Systemization
```

Not:

```
UI → AI → Cloud → Chaos
```

---

## 10. MVP Positioning Statement

> The Aiml-project MVP is a functional system prototype that demonstrates how AI-driven digital public infrastructure platforms can be architected, built, and scaled using privacy-first, modular, and ethical system design principles.

---

## 11. MVP Lock Statement

> Any feature not listed in the **MVP Core Features** section is not part of the MVP and will only be included in later phases.

---
