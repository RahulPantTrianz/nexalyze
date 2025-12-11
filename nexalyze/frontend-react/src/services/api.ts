import axios from 'axios';
import type {
    ApiResponse,
    Company,
    SystemStats,
    HealthStatus,
    Report,
    ReportRequest,
    CompanyAnalysis
} from '../types';

// API base URL - use environment variable in production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: `${API_BASE_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000, // 60 second timeout for AI operations
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('[API Error]', error.response?.data || error.message);
        throw error;
    }
);

// ==================== Company Endpoints ====================

export const searchCompanies = async (
    query: string,
    limit: number = 10
): Promise<ApiResponse<Company[]>> => {
    const response = await api.get('/companies', {
        params: { query, limit }
    });
    return response.data;
};

export const getCompanyDetails = async (
    companyId: number
): Promise<ApiResponse<Company>> => {
    const response = await api.get(`/companies/${companyId}`);
    return response.data;
};

export const analyzeCompany = async (
    companyName: string,
    includeCompetitors: boolean = true
): Promise<ApiResponse<CompanyAnalysis>> => {
    const response = await api.post('/analyze', {
        company_name: companyName,
        include_competitors: includeCompetitors
    });
    return response.data;
};

// ==================== Chat Endpoints ====================

export const sendChatMessage = async (
    query: string,
    sessionId?: string
): Promise<ApiResponse<{ response: string; session_id: string; tools_used: string[] }>> => {
    const response = await api.post('/chat', {
        query,
        user_session: sessionId
    });
    return response.data;
};

// ==================== Report Endpoints ====================

export const generateReport = async (
    request: ReportRequest
): Promise<ApiResponse<Report>> => {
    const response = await api.post('/generate-comprehensive-report', {
        topic: request.topic,
        report_type: request.report_type,
        format: request.format,
        use_langgraph: request.use_langgraph ?? true
    });
    return response.data;
};

export const downloadReport = (filename: string): string => {
    return `${API_BASE_URL}/api/v1/download-report/${filename}`;
};

export const listReports = async (): Promise<ApiResponse<Report[]>> => {
    const response = await api.get('/reports');
    return response.data;
};

// ==================== Stats & Health Endpoints ====================

export const getStats = async (): Promise<ApiResponse<SystemStats>> => {
    const response = await api.get('/stats');
    return response.data;
};

export const getHealthStatus = async (): Promise<HealthStatus> => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
};

// ==================== Data Sync Endpoints ====================

export const syncData = async (
    limit?: number,
    syncAll?: boolean
): Promise<ApiResponse<{ synced_count: number; source: string }>> => {
    const response = await api.post('/sync-data', {
        source: 'yc',
        limit: syncAll ? 0 : (limit || 500),
        sync_all: syncAll
    });
    return response.data;
};

export const getSyncStatus = async (): Promise<ApiResponse<{
    total_companies_in_db: number;
    postgres_connected: boolean;
}>> => {
    const response = await api.get('/sync-data/status');
    return response.data;
};

// ==================== Hacker News Endpoints ====================

export const getHackerNewsMentions = async (
    companyName: string,
    limit: number = 20
): Promise<ApiResponse<any[]>> => {
    const response = await api.post('/hacker-news/company-mentions', {
        company_name: companyName,
        limit
    });
    return response.data;
};

export const getLatestHNStories = async (
    storyType: string = 'top',
    limit: number = 20
): Promise<ApiResponse<any[]>> => {
    const response = await api.get('/hacker-news/latest-stories', {
        params: { story_type: storyType, limit }
    });
    return response.data;
};

export default api;
