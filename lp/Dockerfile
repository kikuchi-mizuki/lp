FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY lp/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire lp directory
COPY lp/ .

EXPOSE 8000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120"]