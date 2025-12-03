FROM python:3.11-slim

WORKDIR /app

# Install WeasyPrint system dependencies
RUN apt-get update && apt-get install -y \
    # Core WeasyPrint dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    libpangoft2-1.0-0 \
    # Font and rendering support
    fontconfig \
    fonts-liberation \
    fonts-dejavu-core \
    libharfbuzz0b \
    libfreetype6 \
    # Image format support
    libjpeg62-turbo \
    libpng16-16 \
    # XML/XSLT support
    libxml2 \
    libxml2-dev \
    libxslt1.1 \
    libxslt1-dev \
    # Additional utilities
    shared-mime-info \
    pkg-config \
    # Build dependencies (needed for some Python packages)
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
