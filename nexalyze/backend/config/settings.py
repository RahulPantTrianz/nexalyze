from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: Optional[str] = None
    serp_api_key: Optional[str] = None
    crunchbase_api_key: Optional[str] = None
    
    # AWS Bedrock Configuration
    aws_profile: str = "amplify"
    aws_region: str = "us-west-2"
    bedrock_model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # Database URLs
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j" 
    neo4j_password: str = "password123"
    postgres_url: str = "postgresql://postgres:password123@localhost:5432/nexalyze"
    redis_url: str = "redis://localhost:6379"

    # External APIs
    yc_api_base_url: str = "https://yc-oss.github.io/api"
    hacker_news_api_base_url: str = "https://hacker-news.firebaseio.com/v0"

    # App Settings
    debug: bool = True
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables

settings = Settings()
