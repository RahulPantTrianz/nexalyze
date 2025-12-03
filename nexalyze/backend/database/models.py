from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import settings

# SQLAlchemy setup
engine = create_engine(settings.postgres_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Startup(Base):
    __tablename__ = "startups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    industry = Column(String)
    founded_year = Column(Integer)
    funding_amount = Column(Float)
    location = Column(String)
    website = Column(String)
    yc_batch = Column(String)
    logo_url = Column(String)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)
    user_session = Column(String)
    results_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class HackerNewsStory(Base):
    __tablename__ = "hacker_news_stories"

    id = Column(Integer, primary_key=True, index=True)
    hn_id = Column(Integer, unique=True, index=True)  # Hacker News item ID
    title = Column(String, index=True)
    url = Column(String)
    score = Column(Integer, default=0)
    by = Column(String)  # Author
    time = Column(Integer)  # Unix timestamp
    descendants = Column(Integer, default=0)  # Number of comments
    text = Column(Text)  # Story text (for Ask HN, Show HN)
    type = Column(String)  # story, job, comment, poll, pollopt
    matched_keywords = Column(JSON)  # Keywords that matched
    matched_in = Column(JSON)  # Where keywords were found (title, text, url)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HackerNewsJob(Base):
    __tablename__ = "hacker_news_jobs"

    id = Column(Integer, primary_key=True, index=True)
    hn_id = Column(Integer, unique=True, index=True)  # Hacker News item ID
    title = Column(String, index=True)
    text = Column(Text)  # Job description
    by = Column(String)  # Author
    time = Column(Integer)  # Unix timestamp
    matched_keywords = Column(JSON)  # Keywords that matched
    matched_in = Column(JSON)  # Where keywords were found
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyHackerNewsMention(Base):
    __tablename__ = "company_hacker_news_mentions"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, index=True)
    hn_story_id = Column(Integer, index=True)  # Reference to HackerNewsStory
    hn_job_id = Column(Integer, index=True)  # Reference to HackerNewsJob
    mention_type = Column(String)  # story, job, show_hn, ask_hn
    matched_keyword = Column(String)
    matched_in = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)
