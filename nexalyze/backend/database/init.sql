-- =============================================================================
-- NEXALYZE - PostgreSQL Database Initialization
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- Companies Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE,
    description TEXT,
    long_description TEXT,
    industry VARCHAR(255),
    location VARCHAR(255),
    website VARCHAR(500),
    founded_year INTEGER,
    yc_batch VARCHAR(50),
    funding VARCHAR(255),
    employees VARCHAR(100),
    stage VARCHAR(100),
    tags TEXT[],
    is_active BOOLEAN DEFAULT true,
    source VARCHAR(100) DEFAULT 'yc',
    source_id VARCHAR(255),
    logo_url VARCHAR(500),
    social_links JSONB,
    team_size INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_location ON companies(location);
CREATE INDEX IF NOT EXISTS idx_companies_yc_batch ON companies(yc_batch);
CREATE INDEX IF NOT EXISTS idx_companies_source ON companies(source);
CREATE INDEX IF NOT EXISTS idx_companies_is_active ON companies(is_active);
CREATE INDEX IF NOT EXISTS idx_companies_tags ON companies USING gin(tags);

-- =============================================================================
-- Company News Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_news (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000),
    source VARCHAR(255),
    published_date TIMESTAMP,
    snippet TEXT,
    sentiment FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_news_company_id ON company_news(company_id);
CREATE INDEX IF NOT EXISTS idx_company_news_published_date ON company_news(published_date);

-- =============================================================================
-- Competitors Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    competitor_name VARCHAR(500) NOT NULL,
    competitor_website VARCHAR(500),
    similarity_score FLOAT,
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_competitors_company_id ON competitors(company_id);

-- =============================================================================
-- Company Analysis Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS company_analysis (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_company_analysis_company_id ON company_analysis(company_id);
CREATE INDEX IF NOT EXISTS idx_company_analysis_type ON company_analysis(analysis_type);

-- =============================================================================
-- Reports Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    topic VARCHAR(500) NOT NULL,
    report_type VARCHAR(100) NOT NULL,
    format VARCHAR(50) NOT NULL,
    file_path VARCHAR(1000),
    file_size BIGINT,
    sections_generated INTEGER DEFAULT 0,
    charts_generated INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);

-- =============================================================================
-- Chat Sessions Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    messages JSONB DEFAULT '[]',
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_activity ON chat_sessions(last_activity);

-- =============================================================================
-- API Usage Stats Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    client_ip VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at);

-- =============================================================================
-- Data Sync Log Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100) NOT NULL,
    synced_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_log_source ON sync_log(source);
CREATE INDEX IF NOT EXISTS idx_sync_log_created_at ON sync_log(created_at);

-- =============================================================================
-- Insert sample data for testing
-- =============================================================================
INSERT INTO companies (name, slug, description, industry, location, founded_year, yc_batch, source)
VALUES 
    ('Nexalyze Demo', 'nexalyze-demo', 'AI-powered startup intelligence platform', 'AI/ML', 'San Francisco, CA', 2024, 'W24', 'manual'),
    ('Sample Fintech', 'sample-fintech', 'Revolutionary payment processing platform', 'FinTech', 'New York, NY', 2023, 'S23', 'manual')
ON CONFLICT (slug) DO NOTHING;

-- =============================================================================
-- Grant permissions
-- =============================================================================
-- Ensure the application user has proper permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nexalyze;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nexalyze;
