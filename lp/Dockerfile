FROM python:3.11-slim

WORKDIR /app

# Install only essential packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir Flask gunicorn

# Copy minimal app
COPY app_minimal.py .

# Create user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set fixed port
ENV PORT=3000
EXPOSE 3000

# Start command with fixed port
CMD gunicorn --bind 0.0.0.0:3000 app_minimal:app
