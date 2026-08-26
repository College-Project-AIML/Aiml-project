-- ============================================================
-- Government Schemes Discovery Platform — PostgreSQL Schema
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Providers (government bodies / ministries)
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    website VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Schemes (main table)
CREATE TABLE IF NOT EXISTS schemes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID REFERENCES providers(id) ON DELETE SET NULL,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    eligibility_text TEXT,
    state_code VARCHAR(10),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    source VARCHAR(255),
    source_type VARCHAR(50),
    link VARCHAR(1000),
    tags TEXT[],
    confidence_score FLOAT DEFAULT 0.0,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Eligibility rules (structured criteria per scheme)
CREATE TABLE IF NOT EXISTS eligibility_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    min_age INT,
    max_age INT,
    max_income DECIMAL(12, 2),
    gender VARCHAR(20)[],
    caste VARCHAR(50)[],
    states VARCHAR(10)[],
    education_level VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Benefits
CREATE TABLE IF NOT EXISTS benefits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    benefit_type VARCHAR(100),
    description TEXT,
    amount DECIMAL(12, 2),
    frequency VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Documents required
CREATE TABLE IF NOT EXISTS documents_required (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Scheme snapshots (live-sync change detection; docs/next.md §2.1)
CREATE TABLE IF NOT EXISTS scheme_snapshots (
    scheme_id UUID PRIMARY KEY REFERENCES schemes(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,             -- sha256 of normalized content fields
    snapshot JSONB,                        -- semantic fields for precise diffs
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    miss_count INT DEFAULT 0,
    source VARCHAR(255) NOT NULL           -- connector key scoping CLOSED detection
);

-- 8. Scheme updates (the "what's new" feed)
CREATE TABLE IF NOT EXISTS scheme_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    change_type VARCHAR(20) NOT NULL,      -- NEW | UPDATED | CLOSED
    changed_fields JSONB,                  -- {"deadline": [old, new]} etc.
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_scheme_updates_detected ON scheme_updates(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheme_updates_scheme   ON scheme_updates(scheme_id);

-- 9. FAQs (chatbot semantic search)
CREATE TABLE IF NOT EXISTS faqs (
    id         SERIAL PRIMARY KEY,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    scheme_id  UUID REFERENCES schemes(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_faqs_scheme_id ON faqs(scheme_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_schemes_name ON schemes(name);
CREATE INDEX IF NOT EXISTS idx_schemes_category ON schemes(category_id);
CREATE INDEX IF NOT EXISTS idx_schemes_provider ON schemes(provider_id);
CREATE INDEX IF NOT EXISTS idx_schemes_state ON schemes(state_code);
CREATE INDEX IF NOT EXISTS idx_schemes_status ON schemes(status);
CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);
CREATE INDEX IF NOT EXISTS idx_eligibility_scheme ON eligibility_rules(scheme_id);
CREATE INDEX IF NOT EXISTS idx_benefits_scheme ON benefits(scheme_id);
CREATE INDEX IF NOT EXISTS idx_documents_scheme ON documents_required(scheme_id);

-- Full-text search index on schemes
CREATE INDEX IF NOT EXISTS idx_schemes_fts ON schemes USING GIN (
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
);
