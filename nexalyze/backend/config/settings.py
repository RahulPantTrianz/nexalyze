"""
Production-Ready Configuration Settings
Uses environment variables with secure defaults for sensitive data
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional, List, Union
import os
import json
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with secure defaults and validation.
    All sensitive data loaded from environment variables.
    """
    
    # ===========================================
    # AI/LLM Configuration
    # ===========================================
    
    # Gemini API Configuration (Primary AI)
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key - REQUIRED for AI features"
    )
    gemini_model: str = Field(
        default="gemini-flash-latest",
        description="Gemini model to use (gemini-flash-latest, gemini-pro-latest, gemini-1.5-pro, gemini-1.5-flash, gemini-pro)"
    )
    
    # AI Model Parameters
    ai_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    ai_max_tokens: int = Field(default=4096, ge=100, le=32000)
    ai_retry_attempts: int = Field(default=5, ge=1, le=10)
    ai_retry_base_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    ai_retry_max_delay: float = Field(default=60.0, ge=1.0, le=300.0)
    
    # ===========================================
    # External API Keys (Optional - enhance features)
    # ===========================================
    
    # SERP API for web search and data enrichment
    serp_api_key: Optional[str] = Field(default=None)
    
    # Data Enrichment APIs
    crunchbase_api_key: Optional[str] = Field(default=None)
    clearbit_api_key: Optional[str] = Field(default=None)
    hunter_api_key: Optional[str] = Field(default=None)
    news_api_key: Optional[str] = Field(default=None)
    
    # Social APIs
    reddit_client_id: Optional[str] = Field(default=None)
    reddit_client_secret: Optional[str] = Field(default=None)
    github_token: Optional[str] = Field(default=None)
    
    # ===========================================
    # Database Configuration
    # ===========================================
    
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password123")
    neo4j_max_connection_pool_size: int = Field(default=50)
    neo4j_connection_timeout: int = Field(default=30)
    
    postgres_url: str = Field(
        default="postgresql://postgres:password123@localhost:5432/nexalyze"
    )
    postgres_pool_size: int = Field(default=20)
    postgres_max_overflow: int = Field(default=10)
    
    redis_url: str = Field(default="redis://localhost:6379")
    redis_max_connections: int = Field(default=100)
    redis_socket_timeout: int = Field(default=30)
    
    # ===========================================
    # External Data Source URLs
    # ===========================================
    
    # Primary Data Sources
    yc_api_base_url: str = "https://yc-oss.github.io/api"
    hacker_news_api_base_url: str = "https://hacker-news.firebaseio.com/v0"
    hacker_news_algolia_url: str = "https://hn.algolia.com/api/v1"
    
    # Startup/Company Directories
    product_hunt_url: str = "https://www.producthunt.com"
    betalist_url: str = "https://betalist.com"
    startup_ranking_url: str = "https://www.startupranking.com"
    
    # Company Registry APIs
    companies_house_url: str = "https://api.company-information.service.gov.uk"
    open_corporates_url: str = "https://api.opencorporates.com/v0.4"
    sec_edgar_url: str = "https://data.sec.gov"
    
    # Market/Economic Data
    world_bank_url: str = "https://api.worldbank.org/v2"
    
    # Tech/Developer Data
    github_api_url: str = "https://api.github.com"
    
    # News and Social
    reddit_api_url: str = "https://www.reddit.com"
    news_api_url: str = "https://newsapi.org/v2"
    google_news_rss: str = "https://news.google.com/rss"
    
    # Financial Data
    alpha_vantage_url: str = "https://www.alphavantage.co"
    yahoo_finance_url: str = "https://query1.finance.yahoo.com"
    
    # Tech Stack Data
    builtwith_url: str = "https://api.builtwith.com"
    stackshare_url: str = "https://stackshare.io"
    g2_url: str = "https://www.g2.com"
    capterra_url: str = "https://www.capterra.com"
    
    # ===========================================
    # Application Settings
    # ===========================================
    
    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json or text
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)
    
    # ===========================================
    # Security Settings
    # ===========================================
    
    # CORS Configuration
    # Store as string to avoid JSON parsing issues
    cors_origins: str = Field(
        default="http://localhost:8501,http://localhost:3000"
    )
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: List[str] = Field(default=["*"])
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)  # requests per minute
    rate_limit_period: int = Field(default=60)  # seconds
    
    # Request Limits
    max_request_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    request_timeout: int = Field(default=60)  # seconds
    
    # API Security
    api_key_header: str = Field(default="X-API-Key")
    require_api_key: bool = Field(default=False)  # Enable in production
    
    # ===========================================
    # Scraping & Data Collection Settings
    # ===========================================
    
    scraper_rate_limit: float = Field(default=2.0)  # seconds between requests
    scraper_timeout: int = Field(default=30)  # seconds
    scraper_max_retries: int = Field(default=3)
    scraper_concurrent_requests: int = Field(default=5)
    
    # Cache Settings
    cache_enabled: bool = Field(default=True)
    cache_ttl_default: int = Field(default=3600)  # 1 hour
    cache_ttl_company: int = Field(default=86400)  # 24 hours
    cache_ttl_search: int = Field(default=300)  # 5 minutes
    
    # ===========================================
    # Report Generation Settings
    # ===========================================
    
    reports_dir: str = Field(default="reports")
    charts_dir: str = Field(default="charts")
    report_cleanup_days: int = Field(default=7)
    max_report_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    
    # ===========================================
    # Feature Flags
    # ===========================================
    
    enable_langgraph: bool = Field(default=True)
    enable_crewai: bool = Field(default=True)
    enable_web_scraping: bool = Field(default=True)
    enable_serp_api: bool = Field(default=True)
    enable_hacker_news: bool = Field(default=True)
    
    # ===========================================
    # Validators
    # ===========================================
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ['development', 'staging', 'production']
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v.upper()
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        # Handle None or empty values
        if v is None or (isinstance(v, str) and not v.strip()):
            return "http://localhost:8501,http://localhost:3000"
        
        # If it's already a string, return as-is
        if isinstance(v, str):
            return v
        
        # If it's a list, convert to comma-separated string
        if isinstance(v, list):
            origins = [str(origin).strip() for origin in v if origin and str(origin).strip()]
            return ','.join(origins) if origins else "http://localhost:8501,http://localhost:3000"
        
        # Fallback to default
        return "http://localhost:8501,http://localhost:3000"
    
    # ===========================================
    # Computed Properties
    # ===========================================
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        return self.environment == 'development'
    
    @property
    def has_serp_api(self) -> bool:
        return bool(self.serp_api_key)
    
    @property
    def has_news_api(self) -> bool:
        return bool(self.news_api_key)
    
    @property
    def has_github_token(self) -> bool:
        return bool(self.github_token)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert cors_origins string to list"""
        if not self.cors_origins or not self.cors_origins.strip():
            return ["http://localhost:8501", "http://localhost:3000"]
        
        # Try to parse as JSON first
        v_stripped = self.cors_origins.strip()
        if v_stripped.startswith('['):
            try:
                parsed = json.loads(self.cors_origins)
                if isinstance(parsed, list):
                    return [origin.strip() for origin in parsed if origin.strip()]
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Treat as comma-separated string
        origins = [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
        return origins if origins else ["http://localhost:8501", "http://localhost:3000"]
    
    def get_cors_origins_for_env(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_production:
            return self.cors_origins_list
        # Allow all in development
        return ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Use this function to access settings throughout the application.
    """
    return Settings()


# Global settings instance for backward compatibility
settings = get_settings()


# ===========================================
# Configuration Validation on Import
# ===========================================

def validate_required_settings():
    """Validate that required settings are configured"""
    warnings = []
    
    if not settings.gemini_api_key:
        warnings.append("GEMINI_API_KEY not set - AI features will be limited")
    
    if settings.is_production:
        if not settings.rate_limit_enabled:
            warnings.append("Rate limiting disabled in production!")
        if "*" in settings.cors_origins:
            warnings.append("CORS allows all origins in production!")
        if settings.debug:
            warnings.append("Debug mode enabled in production!")
    
    return warnings


# Print warnings on import (in development)
if settings.is_development:
    import logging
    logger = logging.getLogger(__name__)
    for warning in validate_required_settings():
        logger.warning(f"Configuration Warning: {warning}")
