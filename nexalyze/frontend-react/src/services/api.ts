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
    timeout: 300000, // 5 minute timeout for AI operations
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

export interface CompanySearchFilters {
    industry?: string;
    location?: string;
    min_year?: number;
    stage?: string;
}

export const searchCompanies = async (
    query: string,
    limit: number = 50,
    filters?: CompanySearchFilters
): Promise<ApiResponse<Company[]>> => {
    const params: Record<string, string | number> = { query, limit };

    if (filters?.industry && filters.industry.toLowerCase() !== 'all') {
        params.industry = filters.industry;
    }
    if (filters?.location) {
        params.location = filters.location;
    }
    if (filters?.min_year) {
        params.min_year = filters.min_year;
    }
    if (filters?.stage) {
        params.stage = filters.stage;
    }

    const response = await api.get('/companies', { params });
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

export interface ChatStreamEvent {
    type: 'start' | 'status' | 'thinking' | 'tool_call' | 'tool' | 'content' | 'complete' | 'end' | 'error';
    message?: string;
    query?: string;
    session_id?: string;
    tool_name?: string;
    tools_used?: string[];
    partial?: boolean;
}

/**
 * Stream chat messages using Server-Sent Events (SSE).
 * The chat API now returns SSE by default for real-time streaming.
 */
export const streamChatMessage = (
    query: string,
    sessionId?: string,
    onEvent?: (event: ChatStreamEvent) => void
): { cancel: () => void } => {
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    // We need to use fetch with POST for SSE since EventSource only supports GET
    const controller = new AbortController();

    const fetchSSE = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query,
                    user_session: sessionId
                }),
                signal: controller.signal
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.slice(6);
                            if (jsonStr.trim()) {
                                const event: ChatStreamEvent = JSON.parse(jsonStr);
                                onEvent?.(event);
                            }
                        } catch (e) {
                            console.error('[SSE] Failed to parse event:', e, line);
                        }
                    }
                }
            }
        } catch (error) {
            if ((error as Error).name !== 'AbortError') {
                console.error('[SSE Chat] Error:', error);
                onEvent?.({ type: 'error', message: String(error) });
            }
        }
    };

    fetchSSE();

    return {
        cancel: () => controller.abort()
    };
};

// Legacy function for backwards compatibility - now uses streaming internally
export const sendChatMessage = async (
    query: string,
    sessionId?: string
): Promise<ApiResponse<{ response: string; session_id: string; tools_used: string[] }>> => {
    return new Promise((resolve, reject) => {
        let finalResponse = '';
        let finalSessionId = sessionId || '';
        let toolsUsed: string[] = [];

        streamChatMessage(query, sessionId, (event) => {
            switch (event.type) {
                case 'content':
                    if (event.message) {
                        finalResponse += event.message + ' ';
                    }
                    break;
                case 'complete':
                    if (event.message) {
                        finalResponse = event.message;
                    }
                    if (event.session_id) {
                        finalSessionId = event.session_id;
                    }
                    if (event.tools_used) {
                        toolsUsed = event.tools_used;
                    }
                    break;
                case 'end':
                    resolve({
                        success: true,
                        data: {
                            response: finalResponse.trim(),
                            session_id: finalSessionId,
                            tools_used: toolsUsed
                        }
                    });
                    break;
                case 'error':
                    reject(new Error(event.message || 'Chat failed'));
                    break;
            }
        });
    });
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

export interface ReportGenerationResult {
    report_filename: string;
    report_path: string;
    topic: string;
    report_type: string;
    format: string;
    charts_generated?: number;
    sections_generated?: number;
    generated_at?: string;
}

export interface ReportTaskStatus {
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress?: number;
    message?: string;
    result?: ReportGenerationResult;
    error?: string;
}

export const generateReportBackground = async (
    request: ReportRequest
): Promise<ApiResponse<{ task_id: string }>> => {
    const response = await api.post('/generate-comprehensive-report-background', {
        topic: request.topic,
        report_type: request.report_type,
        format: request.format,
        use_langgraph: request.use_langgraph ?? true
    });
    return response.data;
};

export const getReportTaskStatus = async (
    taskId: string
): Promise<ApiResponse<ReportTaskStatus>> => {
    const response = await api.get(`/report-tasks/${taskId}`);
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
