-- =============================================================================
-- NEXALYZE - PostgreSQL Database Initialization
-- This script runs automatically on first container startup
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =============================================================================
-- TABLES
-- =============================================================================

-- Companies table for structured company data
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    long_description TEXT,
    industry VARCHAR(255),
    location VARCHAR(255),
    website VARCHAR(500),
    founded_year INTEGER,
    yc_batch VARCHAR(50),
    funding VARCHAR(100),
    employees VARCHAR(100),
    stage VARCHAR(100),
    tags TEXT[],
    source VARCHAR(100) DEFAULT 'internal',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Research queries history
CREATE TABLE IF NOT EXISTS research_queries (
    id SERIAL PRIMARY KEY,
    query_id UUID DEFAULT uuid_generate_v4(),
    user_session VARCHAR(255),
    query_text TEXT NOT NULL,
    query_type VARCHAR(100),
    results JSONB,
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Generated reports
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_id UUID DEFAULT uuid_generate_v4(),
    user_session VARCHAR(255),
    topic TEXT NOT NULL,
    report_type VARCHAR(100),
    format VARCHAR(20),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    sections_count INTEGER,
    charts_count INTEGER,
    status VARCHAR(50) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Hacker News stories cache
CREATE TABLE IF NOT EXISTS hacker_news_stories (
    id SERIAL PRIMARY KEY,
    hn_id BIGINT UNIQUE NOT NULL,
    title TEXT,
    url TEXT,
    score INTEGER,
    by_user VARCHAR(255),
    time_posted TIMESTAMP WITH TIME ZONE,
    story_type VARCHAR(50),
    descendants INTEGER DEFAULT 0,
    raw_data JSONB,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Company mentions in Hacker News
CREATE TABLE IF NOT EXISTS company_hn_mentions (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(500),
    hn_story_id BIGINT REFERENCES hacker_news_stories(hn_id),
    mention_type VARCHAR(50),
    relevance_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, hn_story_id)
);

-- AI chat sessions
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    metadata JSONB
);

-- Chat messages
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id),
    role VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User favorites
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'company', 'report', 'query'
    entity_id VARCHAR(255) NOT NULL,
    entity_name VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, entity_type, entity_id)
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_location ON companies(location);
CREATE INDEX IF NOT EXISTS idx_companies_yc_batch ON companies(yc_batch);
CREATE INDEX IF NOT EXISTS idx_companies_founded_year ON companies(founded_year);
CREATE INDEX IF NOT EXISTS idx_companies_source ON companies(source);
CREATE INDEX IF NOT EXISTS idx_companies_updated_at ON companies(updated_at);

-- Research queries indexes
CREATE INDEX IF NOT EXISTS idx_research_queries_session ON research_queries(user_session);
CREATE INDEX IF NOT EXISTS idx_research_queries_created_at ON research_queries(created_at);
CREATE INDEX IF NOT EXISTS idx_research_queries_type ON research_queries(query_type);

-- Reports indexes
CREATE INDEX IF NOT EXISTS idx_reports_session ON reports(user_session);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);
CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports USING gin(topic gin_trgm_ops);

-- Hacker News indexes
CREATE INDEX IF NOT EXISTS idx_hn_stories_time ON hacker_news_stories(time_posted DESC);
CREATE INDEX IF NOT EXISTS idx_hn_stories_score ON hacker_news_stories(score DESC);
CREATE INDEX IF NOT EXISTS idx_hn_stories_type ON hacker_news_stories(story_type);
CREATE INDEX IF NOT EXISTS idx_hn_mentions_company ON company_hn_mentions(company_name);

-- Chat indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_activity ON chat_sessions(last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);

-- Usage tracking indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_user ON api_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON api_usage(created_at);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for companies table
DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update chat session activity
CREATE OR REPLACE FUNCTION update_chat_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chat_sessions 
    SET last_activity = CURRENT_TIMESTAMP,
        message_count = message_count + 1
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_chat_activity ON chat_messages;
CREATE TRIGGER update_chat_activity
    AFTER INSERT ON chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_activity();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active companies by industry
CREATE OR REPLACE VIEW v_companies_by_industry AS
SELECT 
    industry,
    COUNT(*) as company_count,
    ROUND(AVG(founded_year)) as avg_founded_year,
    array_agg(DISTINCT location) as locations
FROM companies
WHERE is_active = TRUE AND industry IS NOT NULL
GROUP BY industry
ORDER BY company_count DESC;

-- Recent research activity
CREATE OR REPLACE VIEW v_recent_research AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as query_count,
    COUNT(DISTINCT user_session) as unique_sessions,
    AVG(response_time_ms) as avg_response_time
FROM research_queries
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Report statistics
CREATE OR REPLACE VIEW v_report_stats AS
SELECT 
    report_type,
    format,
    COUNT(*) as report_count,
    AVG(file_size_bytes) as avg_file_size,
    AVG(sections_count) as avg_sections,
    AVG(charts_count) as avg_charts
FROM reports
WHERE status = 'completed'
GROUP BY report_type, format;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert initial chat session for system
INSERT INTO chat_sessions (session_id, user_id, metadata)
VALUES ('system', 'system', '{"type": "system", "purpose": "system_operations"}')
ON CONFLICT (session_id) DO NOTHING;

-- =============================================================================
-- GRANTS (adjust as needed for your setup)
-- =============================================================================

-- Grant usage to application user (if different from owner)
-- GRANT USAGE ON SCHEMA public TO nexalyze_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO nexalyze_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nexalyze_app;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Nexalyze database initialization completed successfully!';
END $$;

