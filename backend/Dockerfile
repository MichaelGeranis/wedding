# Multi-stage build for smaller image size
FROM python:3.13-slim as builder

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

# Install dependencies only (not the package itself yet)
RUN uv pip install --system fastapi uvicorn[standard] pydantic pydantic-settings pydantic[email] \
    sqlalchemy asyncpg alembic python-jose[cryptography] passlib[bcrypt] python-multipart \
    slowapi isort greenlet types-python-jose httpx qrcode[pil]

# Production stage
FROM python:3.13-slim

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
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

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
