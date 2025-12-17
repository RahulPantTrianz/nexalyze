"""
Nexalyze Backend API
Production-ready FastAPI application for competitive intelligence and startup research
"""

import asyncio
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings, validate_required_settings
from database.connections import init_databases, postgres_conn, redis_conn
from api.routes import router
from api.exceptions import register_exception_handlers

# ===========================================
# Logging Configuration
# ===========================================

def setup_logging():
    """Configure structured logging based on environment"""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.log_format == "text"
        else '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
    )
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)

# ===========================================
# Global State
# ===========================================

crew_manager = None
startup_time = None


# ===========================================
# Lifespan Management
# ===========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    global crew_manager, startup_time
    startup_time = datetime.utcnow()
    
    logger.info("=" * 60)
    logger.info("Starting Nexalyze Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info("=" * 60)
    
    # Validate configuration
    warnings = validate_required_settings()
    for warning in warnings:
        logger.warning(f"Configuration: {warning}")
    
    # Initialize databases with retry logic
    db_status = await init_databases()
    
    # Initialize CrewAI manager
    try:
        from agents.crew_manager import CrewManager
        crew_manager = CrewManager()
        logger.info("CrewManager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize CrewManager: {e}")
        crew_manager = None
    
    # Load initial data in background (non-blocking)
    if db_status.get("postgres"):
        logger.info("Starting background data sync...")
        try:
            from services.data_service import DataService
            data_service = DataService()
            
            # Sync all companies in background
            asyncio.create_task(
                _safe_data_sync(data_service, limit=None)
            )
            logger.info("Background data sync initiated (ALL companies)")
        except Exception as e:
            logger.warning(f"Could not start background data sync: {e}")
    else:
        logger.warning("Skipping initial data load - PostgreSQL not connected")
    
    logger.info("=" * 60)
    logger.info("Backend startup complete!")
    logger.info(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nexalyze Backend...")
    
    # Close database connections gracefully
    try:
        postgres_conn.close()
        redis_conn.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing connections: {e}")
    
    logger.info("Shutdown complete")


async def _safe_data_sync(data_service, limit: int):
    """Safely execute data sync in background with error handling"""
    try:
        await data_service.sync_yc_data(limit=limit)
        logger.info(f"Background data sync completed ({limit} companies)")
    except Exception as e:
        logger.error(f"Background data sync failed: {e}")


# ===========================================
# FastAPI Application
# ===========================================

app = FastAPI(
    title="Nexalyze API",
    description="""
    AI-powered competitive intelligence and startup research platform.
    
    ## Features
    - 🔍 Company Search & Analysis
    - 📊 Market Research & Reports
    - 🤖 AI-Powered Insights
    - 📈 Competitive Intelligence
    - 🌐 Multi-Source Data Integration
    
    ## Data Sources
    - Y Combinator Companies
    - Hacker News
    - GitHub
    - Product Hunt
    - News APIs
    - And more...
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug or settings.is_development else None,
    redoc_url="/redoc" if settings.debug or settings.is_development else None,
)


# ===========================================
# Exception Handlers Registration
# ===========================================

register_exception_handlers(app)


# ===========================================
# Middleware
# ===========================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_for_env(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Gzip Compression for responses > 1000 bytes
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def request_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global request middleware for:
    - Request ID tracking
    - Request logging
    - Response timing
    - Error handling
    """
    # Generate request ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    # Log request
    start_time = time.time()
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"
        
        # Log response (skip health checks to reduce noise)
        if request.url.path not in ["/health", "/", "/api/v1/health"]:
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"- {response.status_code} ({duration:.2f}ms)"
            )
        
        return response
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- ERROR: {str(e)} ({duration:.2f}ms)"
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "request_id": request_id,
                "message": str(e) if settings.debug else "An error occurred"
            },
            headers={"X-Request-ID": request_id}
        )


# ===========================================
# Rate Limiting Middleware (Simple Implementation)
# ===========================================

# In-memory rate limiting (use Redis in production for distributed systems)
rate_limit_store = {}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    """Simple rate limiting middleware"""
    if not settings.rate_limit_enabled:
        return await call_next(request)
    
    # Get client IP
    client_ip = request.client.host if request.client else "unknown"
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/api/v1/health"]:
        return await call_next(request)
    
    # Check rate limit
    current_time = time.time()
    window_start = current_time - settings.rate_limit_period
    
    # Clean old entries
    if client_ip in rate_limit_store:
        rate_limit_store[client_ip] = [
            t for t in rate_limit_store[client_ip] if t > window_start
        ]
    else:
        rate_limit_store[client_ip] = []
    
    # Check if rate limited
    if len(rate_limit_store[client_ip]) >= settings.rate_limit_requests:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Max {settings.rate_limit_requests} requests per {settings.rate_limit_period} seconds.",
                "retry_after": settings.rate_limit_period
            },
            headers={
                "Retry-After": str(settings.rate_limit_period),
                "X-RateLimit-Limit": str(settings.rate_limit_requests),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    # Record request
    rate_limit_store[client_ip].append(current_time)
    
    response = await call_next(request)
    
    # Add rate limit headers
    remaining = settings.rate_limit_requests - len(rate_limit_store.get(client_ip, []))
    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    
    return response


# ===========================================
# API Routes
# ===========================================

app.include_router(router, prefix="/api/v1")


# ===========================================
# Root Endpoints
# ===========================================

@app.get("/", tags=["System"])
async def root():
    """API root endpoint"""
    return {
        "name": "Nexalyze API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns status of all services.
    """
    global startup_time
    
    # Check database connections
    postgres_healthy = postgres_conn.is_connected() if postgres_conn else False
    redis_healthy = redis_conn.is_connected() if redis_conn else False
    
    # Calculate uptime
    uptime = None
    if startup_time:
        uptime = (datetime.utcnow() - startup_time).total_seconds()
    
    # Overall health status
    all_healthy = postgres_healthy and redis_healthy
    
    health_status = {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
        "environment": settings.environment,
        "uptime_seconds": uptime,
        "services": {
            "postgres": {
                "status": "healthy" if postgres_healthy else "unhealthy",
                "connected": postgres_healthy
            },
            "redis": {
                "status": "healthy" if redis_healthy else "unhealthy",
                "connected": redis_healthy
            },
            "ai": {
                "status": "healthy" if crew_manager else "degraded",
                "provider": "AWS Bedrock",
                "model": settings.bedrock_model_id
            }
        },
        "features": {
            "langgraph_enabled": settings.enable_langgraph,
            "crewai_enabled": settings.enable_crewai,
            "serp_api_available": settings.has_serp_api,
            "news_api_available": settings.has_news_api
        }
    }
    
    # Return appropriate status code
    if all_healthy:
        return health_status
    else:
        return JSONResponse(
            status_code=503,
            content=health_status
        )


@app.get("/ready", tags=["System"])
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.
    Returns 200 only when the service is ready to accept traffic.
    """
    # Check critical services
    postgres_ready = postgres_conn.is_connected() if postgres_conn else False
    
    if postgres_ready:
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "Database connections not established"}
        )


@app.get("/metrics", tags=["System"])
async def metrics():
    """
    Basic metrics endpoint.
    In production, integrate with Prometheus or similar.
    """
    company_count = 0
    
    # Get company count from PostgreSQL
    if postgres_conn.is_connected():
        try:
            results = postgres_conn.query("SELECT COUNT(*) as total FROM companies")
            if results:
                company_count = results[0].get("total", 0)
        except Exception:
            pass
    
    return {
        "companies_indexed": company_count,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# ===========================================
# Main Entry Point
# ===========================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.workers,
        log_level=settings.log_level.lower(),
        access_log=settings.debug
    )
