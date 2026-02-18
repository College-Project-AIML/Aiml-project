# Aiml-project — System Architecture Document

## 1. Architecture Philosophy

Aiml-project follows a **layered, modular, microservices-based architecture** designed for scalability, privacy, intelligence separation, and future national-scale deployment.

Core design principles:

- **Data-first design**
- **Privacy-by-design**
- **AI abstraction**
- **Service isolation**
- **Event-driven flows**
- **Loose coupling**
- **High cohesion**
- **Zero trust security**
- **Scalable by architecture, not hardware**
- **Cloud-agnostic design**

This system is designed to operate **locally-first** (student/low-cost mode) and scale to **cloud-native** (enterprise mode) without architectural changes.

---

## 2. High-Level Architecture Layers

```
┌────────────────────────────┐
│        Frontend Layer       │
├────────────────────────────┤
│        API Gateway Layer    │
├────────────────────────────┤
│      Core Services Layer    │
├────────────────────────────┤
│     Data Intelligence Layer │
├────────────────────────────┤
│       AI/ML Layer           │
├────────────────────────────┤
│    MCP Orchestration Layer  │
├────────────────────────────┤
│        Data Layer           │
├────────────────────────────┤
│   DevOps & System Layer     │
└────────────────────────────┘
```

---

## 3. Layer-wise Architecture

### 3.1 Frontend Layer

**Purpose:** User interaction and visualization

**Components:**

- Citizen Dashboard
- NGO Dashboard
- Admin Dashboard
- Analytics Dashboard
- Profile Management UI
- Scheme Discovery UI

**Responsibilities:**

- Data visualization
- User input capture
- Secure communication
- Role-based rendering
- Consent management UI
- Accessibility
- Multi-language readiness

---

### 3.2 API Gateway Layer

**Purpose:** Central entry point for all requests

**Components:**

- Request routing
- Authentication filter
- Authorization filter
- Rate limiting
- Request validation
- Logging
- Throttling
- API versioning

**Responsibilities:**

- Zero-trust enforcement
- Security boundary
- Traffic control
- Service abstraction
- External exposure control

---

### 3.3 Core Services Layer (Microservices)

**Purpose:** Business logic execution

**Services:**

- Auth Service
- User Service
- Scheme Service
- Eligibility Engine
- Recommendation Service
- Notification Service
- Analytics Service
- Document Service
- Consent Service

**Responsibilities:**

- User management
- Scheme processing
- Eligibility computation
- Profile abstraction
- Notifications
- Access control
- Consent enforcement
- Logging

---

### 3.4 Data Intelligence Layer

**Purpose:** Data processing and intelligence logic

**Components:**

- Data ingestion pipelines
- Data parsers
- Normalization engine
- Deduplication engine
- Classification engine
- Validation engine
- Transformation pipelines
- Event processors

**Responsibilities:**

- Data quality
- Data consistency
- Standardization
- Automated updates
- Data integrity
- Pipeline automation

---

### 3.5 AI/ML Layer

**Purpose:** Intelligence and prediction

**Models:**

- Eligibility prediction model
- Recommendation model
- Skill-demand prediction model
- NLP document parser
- Profile vectorization model
- Similarity engine
- Ranking engine

**Rules:**

- No raw personal data access
- Abstracted profile only
- Privacy firewall enforced
- Explainable outputs
- Ethical model design

---

### 3.6 MCP Orchestration Layer

**Purpose:** System brain and coordination

**Components:**

- Context manager
- Policy engine
- Decision router
- AI orchestration
- Workflow engine
- Priority scheduler
- Service coordination logic

**Responsibilities:**

- Context-aware routing
- Policy enforcement
- Flow optimization
- Decision intelligence
- Load balancing (logic level)
- AI coordination

---

### 3.7 Data Layer

**Purpose:** Persistent storage

**Databases:**

- PostgreSQL → relational data
- Redis → caching, sessions, queues
- Neo4j → relationship graphs
- Vector DB → embeddings & similarity
- Object storage → documents

**Storage Types:**

- Structured data
- Semi-structured data
- Unstructured data
- Graph data
- Vector data

---

### 3.8 DevOps & System Layer

**Purpose:** System stability and automation

**Components:**

- Docker
- Container orchestration
- CI/CD pipelines
- Monitoring
- Logging
- Observability
- Backup systems
- Recovery systems
- Configuration management

---

## 4. Architecture Flow Model

```
User
↓
Frontend
↓
API Gateway
↓
Core Services
↓
Data Intelligence Layer
↓
AI Layer
↓
MCP Layer
↓
Core Services
↓
API Gateway
↓
Frontend
```

---

## 5. Privacy Architecture Integration

```
User Data
↓
Privacy Filter
↓
Data Minimization Engine
↓
Abstraction Layer
↓
AI Models
↓
Recommendation Engine
```

AI never accesses raw personal data.

---

## 6. Security Architecture Integration

```
User
↓
TLS
↓
API Gateway
↓
Auth Layer
↓
RBAC
↓
Service Authorization
↓
Encrypted Storage
↓
Audit Logging
```

---

## 7. Event-Driven Architecture

**Event Types:**

- UserCreated
- ProfileUpdated
- SchemeAdded
- EligibilityComputed
- RecommendationGenerated
- ConsentUpdated
- DataIngested
- ModelUpdated

**Flow:**

```
Service → Event Bus → Subscribers → Processing → Storage
```

---

## 8. Scalability Model

- Horizontal service scaling
- Stateless services
- Load-balanced routing
- Distributed data storage
- Event-based processing
- Asynchronous pipelines
- Modular service expansion

---

## 9. Deployment Model

### Phase 1 (Student Mode):

- Local deployment
- Docker Compose
- GitHub hosting (frontend)
- Local databases
- Local services

### Phase 2 (Scale Mode):

- Kubernetes
- Cloud deployment
- Distributed services
- Auto-scaling
- Multi-region support

---

## 10. Architectural Constraints

- No cloud dependency in early phase
- No paid APIs for MVP
- No real financial systems
- No identity verification systems
- No biometric systems
- No sensitive ID storage
- No surveillance logic

---

## 11. Architecture Governance Rules

- No direct DB access from frontend
- No AI access to raw personal data
- No cross-service tight coupling
- No monolithic services
- No shared databases between services
- No logic in UI
- No business logic in API Gateway
- No direct external API exposure

---

## 12. Architecture Statement

> Aiml-project implements a modular, scalable, privacy-first, AI-driven digital infrastructure architecture designed to simulate national-scale public welfare systems using modern distributed system principles and ethical AI design.

---
