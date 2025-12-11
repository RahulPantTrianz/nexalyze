"""
API Request and Response Schemas
Production-ready Pydantic models for API validation and documentation
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ReportFormat(str, Enum):
    """Supported report formats"""
    PDF = "pdf"
    DOCX = "docx"


class SortOrder(str, Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


class CompanyStage(str, Enum):
    """Company stages"""
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    GROWTH = "growth"
    PUBLIC = "public"
    ACQUIRED = "acquired"


# ============================================================================
# Base Models
# ============================================================================

class BaseAPIModel(BaseModel):
    """Base model with common configurations"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        from_attributes=True,
        populate_by_name=True
    )


class PaginationParams(BaseAPIModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseAPIModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ============================================================================
# Company Models
# ============================================================================

class CompanyBase(BaseAPIModel):
    """Base company model"""
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    description: str = Field(default="", max_length=2000, description="Short description")
    industry: str = Field(default="", max_length=255, description="Industry sector")
    location: str = Field(default="", max_length=255, description="Location")


class CompanyCreate(CompanyBase):
    """Model for creating a company"""
    website: Optional[str] = Field(default=None, max_length=500)
    founded_year: Optional[int] = Field(default=None, ge=1800, le=2030)
    yc_batch: Optional[str] = Field(default=None, max_length=50)
    funding: Optional[str] = Field(default=None, max_length=100)
    employees: Optional[str] = Field(default=None, max_length=50)
    stage: Optional[str] = Field(default=None, max_length=50)
    tags: List[str] = Field(default_factory=list, max_length=20)


class CompanyResponse(CompanyBase):
    """Company response model"""
    id: int = Field(..., description="Company ID")
    website: Optional[str] = None
    founded_year: Optional[int] = None
    yc_batch: Optional[str] = None
    funding: Optional[str] = None
    employees: Optional[str] = None
    stage: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    long_description: Optional[str] = None


class CompanyListResponse(BaseAPIModel):
    """List of companies response"""
    companies: List[CompanyResponse]
    count: int
    query: Optional[str] = None


class CompanyDetailsResponse(CompanyResponse):
    """Detailed company response"""
    long_description: Optional[str] = None
    competitors: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    news: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Search Models
# ============================================================================

class SearchRequest(BaseAPIModel):
    """Company search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Max results")
    industry: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    stage: Optional[str] = Field(default=None, max_length=50)
    min_year: Optional[int] = Field(default=None, ge=1800, le=2030)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError('Query cannot be empty')
        return v


class SearchResponse(BaseAPIModel):
    """Search response"""
    companies: List[CompanyResponse]
    count: int
    query: str
    filters_applied: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Report Models
# ============================================================================

class ReportRequest(BaseAPIModel):
    """Report generation request"""
    topic: str = Field(..., min_length=3, max_length=500, description="Report topic")
    format: ReportFormat = Field(default=ReportFormat.PDF, description="Report format")
    include_charts: bool = Field(default=True, description="Include data visualizations")
    include_competitors: bool = Field(default=True, description="Include competitor analysis")
    max_pages: Optional[int] = Field(default=None, ge=1, le=50, description="Maximum pages")


class ReportResponse(BaseAPIModel):
    """Report generation response"""
    report_id: str
    filename: str
    format: str
    file_path: str
    generated_at: datetime
    topic: str
    status: str = "completed"


class ReportStatusResponse(BaseAPIModel):
    """Report status response"""
    report_id: str
    status: str  # "pending", "generating", "completed", "failed"
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    result: Optional[ReportResponse] = None


# ============================================================================
# Chat Models
# ============================================================================

class ChatMessage(BaseAPIModel):
    """Single chat message"""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[datetime] = None


class ChatRequest(BaseAPIModel):
    """Chat request"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[str] = Field(default=None, max_length=100, description="Session ID for context")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class ChatResponse(BaseAPIModel):
    """Chat response"""
    response: str
    session_id: str
    sources: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamingChatResponse(BaseAPIModel):
    """Streaming chat response chunk"""
    chunk: str
    is_final: bool = False
    session_id: Optional[str] = None


# ============================================================================
# Knowledge Graph Models
# ============================================================================

class GraphNode(BaseAPIModel):
    """Graph node model"""
    id: str
    label: str
    group: str = "default"
    size: int = 20
    color: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseAPIModel):
    """Graph edge model"""
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    label: str = "related"
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphRequest(BaseAPIModel):
    """Knowledge graph request"""
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    depth: int = Field(default=2, ge=1, le=5, description="Graph depth")
    include_competitors: bool = Field(default=True)
    include_investors: bool = Field(default=True)
    include_technologies: bool = Field(default=True)


class KnowledgeGraphResponse(BaseAPIModel):
    """Knowledge graph response"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    company_name: str
    ai_enhanced: bool = False
    total_nodes: int = 0
    total_edges: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Research Models
# ============================================================================

class ResearchRequest(BaseAPIModel):
    """Research request"""
    query: str = Field(..., min_length=3, max_length=1000, description="Research query")
    depth: str = Field(default="standard", pattern="^(quick|standard|comprehensive)$")
    sources: List[str] = Field(default_factory=list, max_length=10)


class ResearchResult(BaseAPIModel):
    """Research result"""
    title: str
    summary: str
    source: str
    url: Optional[str] = None
    relevance_score: float = Field(ge=0, le=1)
    published_date: Optional[datetime] = None


class ResearchResponse(BaseAPIModel):
    """Research response"""
    query: str
    results: List[ResearchResult]
    summary: str
    sources_used: List[str]
    total_results: int
    analysis: Optional[str] = None


# ============================================================================
# Analysis Models
# ============================================================================

class CompanyAnalysisRequest(BaseAPIModel):
    """Company analysis request"""
    company: str = Field(..., min_length=1, max_length=255, description="Company name")
    analysis_type: str = Field(
        default="comprehensive",
        pattern="^(quick|comprehensive|competitive|financial)$"
    )
    include_news: bool = Field(default=True)
    include_social: bool = Field(default=True)


class SWOTAnalysis(BaseAPIModel):
    """SWOT analysis model"""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class MarketPosition(BaseAPIModel):
    """Market position analysis"""
    position: str
    market_share: Optional[float] = Field(default=None, ge=0, le=100)
    growth_rate: Optional[float] = None
    competitive_advantages: List[str] = Field(default_factory=list)


class CompanyAnalysisResponse(BaseAPIModel):
    """Company analysis response"""
    company: str
    summary: str
    swot: Optional[SWOTAnalysis] = None
    market_position: Optional[MarketPosition] = None
    competitors: List[str] = Field(default_factory=list)
    recent_news: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# Sync Models
# ============================================================================

class SyncRequest(BaseAPIModel):
    """Data sync request"""
    source: str = Field(default="yc", pattern="^(yc|all|hacker_news|product_hunt)$")
    limit: Optional[int] = Field(default=None, ge=1, le=10000)
    force: bool = Field(default=False, description="Force resync even if recent")


class SyncStatusResponse(BaseAPIModel):
    """Sync status response"""
    status: str
    synced: int = 0
    skipped: int = 0
    failed: int = 0
    total_available: int = 0
    duration_seconds: float = 0
    last_sync: Optional[datetime] = None
    error: Optional[str] = None


# ============================================================================
# Statistics Models
# ============================================================================

class DashboardStats(BaseAPIModel):
    """Dashboard statistics"""
    total_companies: int = 0
    total_industries: int = 0
    total_locations: int = 0
    recent_syncs: int = 0
    last_sync_time: Optional[datetime] = None


class IndustryDistribution(BaseAPIModel):
    """Industry distribution"""
    industry: str
    count: int
    percentage: float = Field(ge=0, le=100)


class LocationDistribution(BaseAPIModel):
    """Location distribution"""
    location: str
    count: int
    percentage: float = Field(ge=0, le=100)


class StatisticsResponse(BaseAPIModel):
    """Complete statistics response"""
    dashboard: DashboardStats
    industries: List[IndustryDistribution] = Field(default_factory=list)
    locations: List[LocationDistribution] = Field(default_factory=list)
    trends: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Error Models
# ============================================================================

class ErrorDetail(BaseAPIModel):
    """Error detail"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseAPIModel):
    """Standard error response"""
    error: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# ============================================================================
# Health Check Models
# ============================================================================

class ServiceHealth(BaseAPIModel):
    """Individual service health"""
    service: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[float] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseAPIModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime
    services: List[ServiceHealth] = Field(default_factory=list)
    uptime_seconds: float = 0


# ============================================================================
# Hacker News Models
# ============================================================================

class HackerNewsItem(BaseAPIModel):
    """Hacker News item"""
    id: int
    title: str
    url: Optional[str] = None
    score: int = 0
    by: str = ""
    time: int
    type: str
    descendants: int = 0


class HackerNewsMention(BaseAPIModel):
    """Company mention in Hacker News"""
    story: HackerNewsItem
    relevance_score: float = Field(ge=0, le=1)
    sentiment: str = Field(default="neutral", pattern="^(positive|negative|neutral)$")


class HackerNewsResponse(BaseAPIModel):
    """Hacker News response"""
    company: str
    mentions: List[HackerNewsMention] = Field(default_factory=list)
    total_mentions: int = 0
    average_score: float = 0
    sentiment_summary: Dict[str, int] = Field(default_factory=dict)


# ============================================================================
# Competitive Intelligence Models
# ============================================================================

class CompetitorInfo(BaseAPIModel):
    """Competitor information"""
    name: str
    description: str
    market_share: Optional[float] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class CompetitiveIntelligenceRequest(BaseAPIModel):
    """Competitive intelligence request"""
    company: str = Field(..., min_length=1, max_length=255)
    max_competitors: int = Field(default=5, ge=1, le=20)
    include_metrics: bool = Field(default=True)


class CompetitiveIntelligenceResponse(BaseAPIModel):
    """Competitive intelligence response"""
    company: str
    competitors: List[CompetitorInfo]
    market_analysis: str
    competitive_landscape: str
    recommendations: List[str] = Field(default_factory=list)

