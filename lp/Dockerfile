FROM python:3.11-slim

WORKDIR /app

# Install system dependencies in a single layer to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --compile -r requirements.txt && \
    pip cache purge

# Copy the entire application
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set default port if not provided
ENV PORT=3000

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/ping || exit 1

# Use environment variable for port with fallback
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --preload wsgi:app