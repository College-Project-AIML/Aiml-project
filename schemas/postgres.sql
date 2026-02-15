-- Enable UUID extension for secure IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. ENUMS (Standardizing choices)
CREATE TYPE user_role AS ENUM ('citizen', 'admin', 'ngo');
CREATE TYPE gender_type AS ENUM ('male', 'female', 'transgender', 'other');
CREATE TYPE caste_category AS ENUM ('general', 'obc', 'sc', 'st', 'other');

-- 2. USERS TABLE (Auth details)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15),
    password_hash VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'citizen',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PROFILES TABLE (The "AI Context" - Critical for Eligibility)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Demographic Data
    dob DATE,
    gender gender_type,
    caste caste_category,
    disability_status BOOLEAN DEFAULT FALSE,
    disability_percentage INT DEFAULT 0,
    
    -- Location (For state-specific schemes)
    state VARCHAR(100),
    district VARCHAR(100),
    is_rural BOOLEAN DEFAULT TRUE, -- Rural/Urban focus is key for schemes
    
    -- Economic Data
    annual_income DECIMAL(12, 2) DEFAULT 0,
    employment_status VARCHAR(100), -- e.g., 'student', 'unemployed', 'farmer'
    occupation_sector VARCHAR(100), -- e.g., 'agriculture', 'construction'
    
    -- Education
    education_level VARCHAR(100), -- e.g., '10th_pass', 'graduate'
    
    UNIQUE(user_id)
);

-- 4. APPLICATION TRACKING (What have they applied for?)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    scheme_id VARCHAR(255) NOT NULL, -- References MongoDB ID
    status VARCHAR(50) DEFAULT 'applied', -- applied, approved, rejected
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);