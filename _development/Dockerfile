# Multi-stage build for Local Agent v4.0

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY local_agent/ ./local_agent/
COPY --from=frontend-builder /app/frontend/dist ./local_agent/web/static/

# Create directories
RUN mkdir -p /app/data /app/plugins /app/sandbox

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data
ENV PLUGINS_DIR=/app/plugins
ENV SANDBOX_PATH=/app/sandbox

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/analytics || exit 1

# Run the application
CMD ["python", "-m", "local_agent.web.app"]
