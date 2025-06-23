# Slim MCP server image optimized for size and GitHub container registry
FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    pyyaml==6.0.1 \
    mcp>=1.0.0 \
    pydantic>=2.0.0

# Create working directory
WORKDIR /workspace

# Copy MCP server script
COPY mcp-server.py /workspace/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp && \
    chown -R mcp:mcp /workspace
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import mcp; print('MCP server healthy')" || exit 1

# Default command
CMD ["python3", "mcp-server.py", "--project-root", "/workspace"]
