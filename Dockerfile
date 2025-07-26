FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Environment variables (do NOT override credentials path here)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better cache usage
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Start app using Gunicorn with Uvicorn workers
CMD exec gunicorn --bind :$PORT main:app --workers 1 --threads 8 --timeout 0
