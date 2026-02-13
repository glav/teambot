# TeamBot Docker Image
# 
# Usage:
#   docker build -t teambot docker/
#   docker run -it -v $(pwd):/workspace teambot run
#   docker run --rm teambot --help

FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Install TeamBot
RUN uv tool install copilot-teambot

# Add tool bin to PATH
ENV PATH="/root/.local/bin:$PATH"

# Verify installation
RUN teambot --version

# Create workspace directory
WORKDIR /workspace

# Set default command
ENTRYPOINT ["teambot"]
CMD ["--help"]

# Labels
LABEL org.opencontainers.image.title="TeamBot"
LABEL org.opencontainers.image.description="Autonomous AI agent teams for software development"
LABEL org.opencontainers.image.url="https://github.com/teambot-ai/teambot"
LABEL org.opencontainers.image.source="https://github.com/teambot-ai/teambot"
LABEL org.opencontainers.image.licenses="MIT"
