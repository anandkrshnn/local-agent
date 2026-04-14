#!/bin/bash
# LocalAgent v0.1.0 — 1-click sovereign AI

set -e

echo "🛡️ Launching LocalAgent v0.1.0..."
DEFAULT_IMAGE="ghcr.io/anandkrshnn/local-agent:v0.1.0"
DEFAULT_TAG="v0.1.0"

# Create vaults dir
mkdir -p ~/local-agent/vaults

# Run container
docker run -d \
  --name local-agent \
  -p 8000:8000 \
  -v $HOME/local-agent/vaults:/app/vaults \
  --restart unless-stopped \
  anandkrshnn/local-agent:v0.1.0

echo "✅ Live: http://localhost:8000"
echo "📁 Vaults: $HOME/local-agent/vaults"
echo "🛑 Stop: docker stop local-agent"
echo "🗑️  Clean: docker rm local-agent"
