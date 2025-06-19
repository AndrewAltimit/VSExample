# Base image with development tools
FROM --platform=linux/amd64 ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system tools
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    wget \
    curl \
    gpg \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN type -p curl >/dev/null || (apt update && apt install curl -y) \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt update \
    && apt install gh -y \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    pyyaml \
    json5 \
    mcp>=1.0.0 \
    pydantic>=2.0.0

# Create working directory
WORKDIR /workspace

# Default to bash for interactive use
CMD ["/bin/bash"]