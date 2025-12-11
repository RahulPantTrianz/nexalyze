"""
Nexalyze Services Module
Provides comprehensive market research and competitive intelligence capabilities
"""

from services.gemini_service import (
    GeminiService,
    get_gemini_service,
    generate_ai_response,
    analyze_company_with_ai,
    discover_competitors_with_ai
)

from services.data_sources_external import (
    DataSources,
    get_data_sources
)

from services.competitive_intelligence_service import (
    CompetitiveIntelligenceService,
    competitive_intel_service
)

from services.report_service import ReportService
from services.research_service import ResearchService
from services.data_service import DataService
from services.web_scraper_service import ScraperService
from services.hacker_news_service import HackerNewsService

__all__ = [
    # Gemini AI Service
    'GeminiService',
    'get_gemini_service',
    'generate_ai_response',
    'analyze_company_with_ai',
    'discover_competitors_with_ai',
    
    # External Data Sources
    'DataSources',
    'get_data_sources',
    
    # Competitive Intelligence
    'CompetitiveIntelligenceService',
    'competitive_intel_service',
    
    # Core Services
    'ReportService',
    'ResearchService',
    'DataService',
    'ScraperService',
    'HackerNewsService',
]
