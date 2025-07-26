FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements first for better cache usage
COPY requirements.txt .

# Install dependencies and verify uvicorn
RUN pip install --no-cache-dir -r requirements.txt && \
    pip show uvicorn || { echo "Uvicorn installation failed"; exit 1; }

# Copy application code
COPY . .

# Copy Firebase credentials (if needed, adjust based on your setup)
COPY firebase.json /tmp/firebase.json

# Verify uvicorn is executable
RUN which uvicorn || { echo "uvicorn not found in PATH"; exit 1; }

# Start app using Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT