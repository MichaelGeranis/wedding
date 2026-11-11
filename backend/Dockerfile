# Multi-stage build for smaller image size
FROM python:3.14-slim AS builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Install the runtime dependencies declared in pyproject.toml (not the package
# itself, which runs from /app/src) into a virtualenv copied to the final stage.
RUN uv venv /opt/venv \
    && uv pip install --python /opt/venv --no-cache -r pyproject.toml

# Production stage
FROM python:3.14-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Copy application code
COPY . .

# Set Python path to include the src directory
ENV PYTHONPATH=/app/src

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["uvicorn", "wedding_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
