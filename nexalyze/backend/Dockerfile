# ============================================================================
# NEXALYZE BACKEND - PRODUCTION DOCKERFILE
# Multi-stage build for optimized, secure production deployment
# ============================================================================

# ============================================================================
# Stage 1: Build dependencies
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxml2-dev \
    libxslt1-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first (layer caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install requirements with retries
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_RETRIES=10
ENV PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir -r requirements.txt || \
    (sleep 30 && pip install --no-cache-dir -r requirements.txt) || \
    (sleep 60 && pip install --no-cache-dir -r requirements.txt)


# ============================================================================
# Stage 2: Production image
# ============================================================================
FROM python:3.11-slim as production

# Labels for container metadata
LABEL maintainer="Nexalyze Team"
LABEL version="2.0.0"
LABEL description="Nexalyze AI-powered competitive intelligence API"

# Create non-root user for security
RUN groupadd --gid 1000 nexalyze && \
    useradd --uid 1000 --gid nexalyze --shell /bin/bash --create-home nexalyze

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint runtime dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libpangoft2-1.0-0 \
    # Font support
    fontconfig \
    fonts-liberation \
    fonts-dejavu-core \
    libharfbuzz0b \
    libfreetype6 \
    # Image format support
    libjpeg62-turbo \
    libpng16-16 \
    # XML support
    libxml2 \
    libxslt1.1 \
    # Utilities
    shared-mime-info \
    curl \
    # Security updates
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

# Application environment variables (defaults, override at runtime)
ENV HOST=0.0.0.0 \
    PORT=8000 \
    WORKERS=1 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production

# Copy application code
COPY --chown=nexalyze:nexalyze . .

# Create directories for reports and logs
RUN mkdir -p /app/reports /app/logs /app/cache && \
    chown -R nexalyze:nexalyze /app

# Switch to non-root user
USER nexalyze

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production startup command
# Use single worker by default to avoid multiprocessing issues in Docker
# Set WORKERS > 1 in environment to use multiple workers
CMD ["sh", "-c", "if [ \"${WORKERS:-1}\" -gt 1 ] && [ \"$ENVIRONMENT\" != \"development\" ]; then uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKERS} --log-level $(echo ${LOG_LEVEL} | tr '[:upper:]' '[:lower:]') --access-log --proxy-headers; else uvicorn main:app --host ${HOST} --port ${PORT} --log-level $(echo ${LOG_LEVEL} | tr '[:upper:]' '[:lower:]') --access-log --proxy-headers; fi"]


# ============================================================================
# Stage 3: Development image (optional, for local dev)
# ============================================================================
FROM production as development

# Switch to root for dev tool installation
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install dev dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy

# Switch back to nexalyze user
USER nexalyze

# Development environment variables
ENV ENVIRONMENT=development \
    DEBUG=true \
    LOG_LEVEL=DEBUG

# Development startup with hot reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]
