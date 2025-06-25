# WikiJS MCP Server Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r wikijs && useradd -r -g wikijs wikijs

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        nano \
        vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY pyproject.toml ./
COPY wikijs_mcp/__init__.py ./wikijs_mcp/

# Install Python dependencies
RUN pip install -e .

# Copy application code
COPY . .

# Create directory for encrypted config
RUN mkdir -p /app/config && \
    chown -R wikijs:wikijs /app

# Switch to non-root user
USER wikijs

# Expose MCP server port (not HTTP, but for documentation)
EXPOSE 3000

# Create entrypoint script
COPY --chown=wikijs:wikijs docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["server"]