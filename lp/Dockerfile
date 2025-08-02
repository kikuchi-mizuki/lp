FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

EXPOSE $PORT

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"]