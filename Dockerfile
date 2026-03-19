# Stage 1: Builder
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Install dependencies to a temporary location
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Set labels
LABEL maintainer="SmartLamp Team"
LABEL version="1.0.0"
LABEL description="Smart Lamp Control API - FastAPI"

# Create non-root user
RUN groupadd -r smartlamp && useradd -r -g smartlamp smartlamp

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app ./app
COPY pyproject.toml ./

# Ensure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R smartlamp:smartlamp /app

# Switch to non-root user
USER smartlamp

# Expose ports
# 8000 - HTTP API
# 41328 - UDP discovery
# 41330 - TCP control
EXPOSE 8000 41328 41330

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
