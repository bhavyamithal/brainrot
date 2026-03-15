# Brainrot Platform Docker Image
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install FFmpeg and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ffmpeg -version

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY brainrot/ ./brainrot/
COPY pyproject.toml ./

# Create necessary directories
RUN mkdir -p /app/cache /app/credentials /app/output /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BRAINROT_CACHE_DIR=/app/cache \
    BRAINROT_OUTPUT_DIR=/app/output \
    BRAINROT_LOG_DIR=/app/logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from brainrot.video.assembly import check_ffmpeg_available; check_ffmpeg_available()" || exit 1

# Default entrypoint
ENTRYPOINT ["brainrot"]
CMD ["--help"]
