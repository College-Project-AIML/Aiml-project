-- ============================================================
-- User Interaction Events for ML Training
-- ============================================================

-- 1. User events table (captures all interactions for training data)
CREATE TABLE IF NOT EXISTS user_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    scheme_id UUID REFERENCES schemes(id) ON DELETE SET NULL,
    event_type VARCHAR(30) NOT NULL,  -- 'view', 'click', 'apply_start', 'apply_complete', 'bookmark', 'share', 'search', 'filter'
    metadata JSONB DEFAULT '{}',       -- {position: 3, source: 'recommended', dwell_ms: 5000, query: 'scholarship'}
    session_id UUID,                   -- for grouping events in a session
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_events_scheme ON user_events(scheme_id);
CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
CREATE INDEX IF NOT EXISTS idx_user_events_created ON user_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_events_session ON user_events(session_id);

-- 2. User profile snapshots (for point-in-time training features)
CREATE TABLE IF NOT EXISTS user_profile_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    age INT,
    income NUMERIC(12, 2),
    gender VARCHAR(20),
    caste VARCHAR(50),
    state VARCHAR(10),
    education_level VARCHAR(100),
    source VARCHAR(50) DEFAULT 'onboarding',  -- 'onboarding', 'profile_update', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profile_snapshots_user ON user_profile_snapshots(user_id, created_at DESC);

-- 3. User preferences (derived from interactions for quick access)
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

-- 4. ML Training dataset materialized view (for efficient training data extraction)
CREATE MATERIALIZED VIEW IF NOT EXISTS ml_training_data AS
SELECT
    ue.id AS event_id,
    ue.user_id,
    ue.scheme_id,
    ue.event_type,
    ue.metadata,
    ue.created_at AS event_time,
    -- User profile at event time (latest snapshot before event)
    ups.age,
    ups.income,
    ups.gender,
    ups.caste,
    ups.state,
    ups.education_level,
    -- Scheme features
    s.state_code AS scheme_state_code,
    s.source AS scheme_source,
    s.confidence_score,
    -- Eligibility rules
    er.min_age,
    er.max_age,
    er.max_income,
    er.gender AS rule_gender,
    er.caste AS rule_caste,
    er.states AS rule_states,
    er.education_level AS rule_education_level,
    -- Label: positive if meaningful engagement
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

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_ml_training_data()
RETURNS VOID LANGUAGE sql AS $$
    REFRESH MATERIALIZED VIEW CONCURRENTLY ml_training_data;
$$;