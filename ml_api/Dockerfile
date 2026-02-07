# =============================================================================
# ML API Dockerfile
# =============================================================================
#
# DOCKERFILE BASICS:
# ------------------
# A Dockerfile is a recipe for building a container image.
# Each instruction creates a layer. Layers are cached for faster rebuilds.
#
# BEST PRACTICES USED:
# 1. Use specific Python version (not just "python:3")
# 2. Use slim image (smaller, fewer vulnerabilities)
# 3. Don't run as root (security)
# 4. Copy requirements first (better layer caching)
# 5. Use multi-stage builds for production (not needed here, but good to know)
#
# =============================================================================

# -----------------------------------------------------------------------------
# BASE IMAGE
# -----------------------------------------------------------------------------
# python:3.11-slim is:
# - Official Python image
# - Debian-based (stable)
# - "slim" = minimal packages (smaller image)
FROM python:3.11-slim

# -----------------------------------------------------------------------------
# LABELS (Metadata)
# -----------------------------------------------------------------------------
# Labels add metadata to the image (visible in docker inspect)
LABEL maintainer="your-email@example.com"
LABEL description="Iris Classifier ML API with Prometheus metrics"
LABEL version="1.0.0"

# -----------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
# -----------------------------------------------------------------------------
# PYTHONDONTWRITEBYTECODE: Don't create .pyc files (smaller image)
# PYTHONUNBUFFERED: Send output directly to terminal (see logs immediately)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -----------------------------------------------------------------------------
# WORKING DIRECTORY
# -----------------------------------------------------------------------------
# All subsequent commands run from this directory
# Creates /app if it doesn't exist
WORKDIR /app

# -----------------------------------------------------------------------------
# INSTALL DEPENDENCIES
# -----------------------------------------------------------------------------
# Copy requirements first (separate from code)
# This layer is cached - only rebuilds when requirements.txt changes
# This means code changes don't trigger dependency reinstall
COPY requirements.txt .

# Install Python packages
# --no-cache-dir: Don't cache pip packages (smaller image)
# --upgrade: Ensure latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# COPY APPLICATION CODE
# -----------------------------------------------------------------------------
# Copy everything in the current directory to /app
# This layer changes when any code changes
COPY . .

# -----------------------------------------------------------------------------
# CREATE NON-ROOT USER
# -----------------------------------------------------------------------------
# Security: Don't run as root inside the container
# If the app is compromised, attacker has limited permissions
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# -----------------------------------------------------------------------------
# EXPOSE PORT
# -----------------------------------------------------------------------------
# Document which port the app listens on
# This doesn't actually publish the port - that's done with -p flag or compose
EXPOSE 8000

# -----------------------------------------------------------------------------
# HEALTH CHECK
# -----------------------------------------------------------------------------
# Docker can automatically check if container is healthy
# If health check fails, container is marked unhealthy
# Orchestrators (Docker Swarm, Kubernetes) use this for rolling updates
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# -----------------------------------------------------------------------------
# RUN COMMAND
# -----------------------------------------------------------------------------
# CMD = default command when container starts
# Using uvicorn directly (not "python app.py") for production
# --host 0.0.0.0: Listen on all interfaces (required for Docker)
# --port 8000: Port to listen on
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
