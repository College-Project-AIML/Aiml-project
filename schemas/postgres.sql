-- ============================================================
-- Government Schemes Discovery Platform — PostgreSQL Schema
-- Compatible with PostgreSQL 13+ (Neon, RDS, Supabase, Local)
-- ============================================================

-- 1. Providers (government bodies / ministries)
CREATE TABLE IF NOT EXISTS providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    website VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Schemes (main table)
CREATE TABLE IF NOT EXISTS schemes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    document_name VARCHAR(255) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Scheme snapshots (live-sync change detection)
CREATE TABLE IF NOT EXISTS scheme_snapshots (
    scheme_id UUID PRIMARY KEY REFERENCES schemes(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    snapshot JSONB,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    miss_count INT DEFAULT 0,
    source VARCHAR(255) NOT NULL
);

-- 8. Scheme updates (feed)
CREATE TABLE IF NOT EXISTS scheme_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_id UUID NOT NULL REFERENCES schemes(id) ON DELETE CASCADE,
    change_type VARCHAR(20) NOT NULL,
    changed_fields JSONB,
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

-- 10. Users (authentication and saved profile)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    age INT,
    income NUMERIC(12, 2),
    gender VARCHAR(20),
    caste VARCHAR(50),
    education VARCHAR(100),
    state VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    oauth_provider VARCHAR(20),
    oauth_id VARCHAR(255),
    avatar_url VARCHAR(500)
);
CREATE INDEX IF NOT EXISTS ix_users_oauth ON users(oauth_provider, oauth_id);

-- Full-text search index on schemes
CREATE INDEX IF NOT EXISTS idx_schemes_fts ON schemes USING GIN (
    to_tsvector('english', COALESCE(name, '') || ' ' || COALESCE(description, ''))
);

-- 11. User Interaction Events for ML Training
CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    scheme_id UUID REFERENCES schemes(id) ON DELETE SET NULL,
    event_type VARCHAR(30) NOT NULL,
    metadata JSONB DEFAULT '{}',
    session_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_events_scheme ON user_events(scheme_id);
CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_user_events_created ON user_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_events_session ON user_events(session_id);

-- 12. User profile snapshots (point-in-time features)
CREATE TABLE IF NOT EXISTS user_profile_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    age INT,
    income NUMERIC(12, 2),
    gender VARCHAR(20),
    caste VARCHAR(50),
    state VARCHAR(10),
    education_level VARCHAR(100),
    source VARCHAR(50) DEFAULT 'onboarding',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profile_snapshots_user ON user_profile_snapshots(user_id, created_at DESC);

-- 13. User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY,
    preferred_categories TEXT[] DEFAULT '{}',
    preferred_states TEXT[] DEFAULT '{}',
    preferred_benefit_types TEXT[] DEFAULT '{}',
    avg_dwell_ms INT,
    total_views INT DEFAULT 0,
    total_clicks INT DEFAULT 0,
    total_applications INT DEFAULT 0,
    last_active_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 14. ML Training dataset materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS ml_training_data AS
SELECT
    ue.id AS event_id,
    ue.user_id,
    ue.scheme_id,
    ue.event_type,
    ue.metadata,
    ue.created_at AS event_time,
    ups.age,
    ups.income,
    ups.gender,
    ups.caste,
    ups.state,
    ups.education_level,
    s.state_code AS scheme_state_code,
    s.source AS scheme_source,
    s.confidence_score,
    er.min_age,
    er.max_age,
    er.max_income,
    er.gender AS rule_gender,
    er.caste AS rule_caste,
    er.states AS rule_states,
    er.education_level AS rule_education_level,
    CASE
        WHEN ue.event_type IN ('apply_complete', 'bookmark') THEN 1
        WHEN ue.event_type = 'apply_start' THEN 1
        WHEN ue.event_type = 'click' AND (ue.metadata->>'dwell_ms')::int > 30000 THEN 1
        WHEN ue.event_type = 'view' AND (ue.metadata->>'dwell_ms')::int > 60000 THEN 1
        ELSE 0
    END AS label
FROM user_events ue
JOIN schemes s ON s.id = ue.scheme_id
LEFT JOIN eligibility_rules er ON er.scheme_id = s.id
LEFT JOIN LATERAL (
    SELECT * FROM user_profile_snapshots ups
    WHERE ups.user_id = ue.user_id AND ups.created_at <= ue.created_at
    ORDER BY ups.created_at DESC LIMIT 1
) ups ON true
WHERE ue.scheme_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_ml_training_data_label ON ml_training_data(label);
CREATE INDEX IF NOT EXISTS idx_ml_training_data_user ON ml_training_data(user_id);
CREATE INDEX IF NOT EXISTS idx_ml_training_data_time ON ml_training_data(event_time);

CREATE OR REPLACE FUNCTION refresh_ml_training_data()
RETURNS VOID LANGUAGE sql AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data;
$$;
