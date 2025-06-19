#!/bin/bash
# run_claude.sh - Start Claude Code with Node.js 22.16.0

set -e

echo "🚀 Starting Claude Code with Node.js 22.16.0"

# Load NVM if it exists
if [ -s "$HOME/.nvm/nvm.sh" ]; then
    echo "📦 Loading NVM..."
    source "$HOME/.nvm/nvm.sh"
elif [ -s "/usr/local/share/nvm/nvm.sh" ]; then
    echo "📦 Loading NVM (system-wide)..."
    source "/usr/local/share/nvm/nvm.sh"
else
    echo "❌ NVM not found. Please install NVM first."
    echo "Visit: https://github.com/nvm-sh/nvm#installation-and-update"
    exit 1
fi

# Use Node.js 22.16.0
echo "🔧 Switching to Node.js 22.16.0..."
nvm use 22.16.0

# Verify Node version
NODE_VERSION=$(node --version)
echo "✅ Using Node.js: $NODE_VERSION"

# Start Claude Code
echo "🤖 Starting Claude Code..."
echo "MCP Server: Available via docker-compose up -d mcp-server"
echo ""

claude