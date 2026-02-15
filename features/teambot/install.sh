#!/usr/bin/env bash
set -e

VERSION="${VERSION:-latest}"

echo "Installing TeamBot v${VERSION}..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install TeamBot to global directories so it's available to all users
# UV_TOOL_BIN_DIR: where executables are placed
# UV_TOOL_DIR: where tool environments are stored
export UV_TOOL_BIN_DIR=/usr/local/bin
export UV_TOOL_DIR=/usr/local/share/uv

if [ "$VERSION" = "latest" ]; then
    uv tool install copilot-teambot
else
    uv tool install "copilot-teambot==$VERSION"
fi

echo "TeamBot installed successfully!"
teambot --version || echo "Note: You may need to restart your shell for PATH changes to take effect."
