FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies only (no system dependencies)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set default port if not provided
ENV PORT=3000

EXPOSE $PORT

# Use environment variable for port with fallback
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-3000} --workers 1 --timeout 120 --preload"]