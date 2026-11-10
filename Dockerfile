# ==============================================================================
# KiranaVaani (किरानावाणी) — Production Dockerfile for Render
# Multi-Stage Build: Node.js 20 (Vite Frontend) + Python 3.11 (FastAPI Backend)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React/Vite Frontend Cockpit
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci || npm install

# Build production assets into frontend/dist
COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Python Backend Runtime & Unified Static Asset Server
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner
WORKDIR /app

# Configure Python execution environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000

# Install minimal runtime dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, data catalogues, audio samples and configuration
COPY backend/ ./backend/
COPY data/ ./data/
COPY audio_samples/ ./audio_samples/

# Copy compiled frontend distribution from Stage 1 for unified serving
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create non-privileged user and group for container isolation
RUN adduser --disabled-password --gecos "" --home /app appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose Render default port
EXPOSE 10000

# Container healthcheck using KiranaVaani's /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/health || exit 1

# Start production Uvicorn server bound to 0.0.0.0 on Render's dynamic PORT
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
