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

# Install TeamBot
if [ "$VERSION" = "latest" ]; then
    uv tool install copilot-teambot
else
    uv tool install "copilot-teambot==$VERSION"
fi

# Ensure tool bin is in PATH for all shells
if [ -d /etc/profile.d ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' > /etc/profile.d/teambot.sh
fi

# Also add to bashrc for non-login shells
if [ -f /etc/bash.bashrc ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> /etc/bash.bashrc
fi

echo "TeamBot installed successfully!"
teambot --version || echo "Note: You may need to restart your shell for PATH changes to take effect."
