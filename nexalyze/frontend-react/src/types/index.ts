// Company types
export interface Company {
    id: number;
    name: string;
    description: string;
    industry: string;
    location: string;
    website: string;
    founded_year: number;
    yc_batch: string;
    funding: string;
    employees: string;
    stage: string;
    tags: string[];
    long_description: string;
    is_active: boolean;
    source: string;
}

// Search types
export interface SearchFilters {
    industry?: string;
    location?: string;
    stage?: string;
    minFunding?: number;
    maxFunding?: number;
}

export interface SearchResult {
    companies: Company[];
    total: number;
    page: number;
    limit: number;
}

// Chat types
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    tools_used?: string[];
}

export interface ChatSession {
    id: string;
    messages: ChatMessage[];
    created_at: Date;
}

// Report types
export interface Report {
    id: string;
    filename: string;
    topic: string;
    report_type: 'comprehensive' | 'competitive_analysis' | 'market_research';
    format: 'pdf' | 'docx';
    created_at: Date;
    sections_generated: number;
    charts_generated: number;
}

export interface ReportRequest {
    topic: string;
    report_type: string;
    format: string;
    use_langgraph?: boolean;
}

// Analysis types
export interface CompanyAnalysis {
    company: Company;
    competitors: Company[];
    swot: {
        strengths: string[];
        weaknesses: string[];
        opportunities: string[];
        threats: string[];
    };
    market_size: string;
    market_growth: string;
    news: NewsItem[];
}

export interface NewsItem {
    title: string;
    url: string;
    source: string;
    date: string;
    snippet: string;
}

// API Response types
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
    message?: string;
}

// Stats types
export interface SystemStats {
    total_companies: number;
    total_queries: number;
    total_reports: number;
    data_sources: number;
}

// Health types
export interface HealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    timestamp: string;
    version: string;
    environment: string;
    uptime_seconds: number;
    services: {
        postgres: { status: string; connected: boolean };
        redis: { status: string; connected: boolean };
        ai: { status: string; provider: string; model: string };
    };
    features: {
        langgraph_enabled: boolean;
        crewai_enabled: boolean;
        serp_api_available: boolean;
        news_api_available: boolean;
    };
}
