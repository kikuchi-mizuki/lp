FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies with retry mechanism
RUN apk update && \
    apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    && rm -rf /var/cache/apk/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with retry mechanism
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create non-root user for security
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set default port if not provided
ENV PORT=3000

EXPOSE $PORT

# Use environment variable for port with fallback
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-3000} --workers 1 --timeout 120 --preload"]