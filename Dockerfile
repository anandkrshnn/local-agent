# 🛡️ LocalAgent Sovereign AI Container (v0.1.0)
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the project files
COPY . /app

# Install the package and dependencies
# This includes lancedb and pyarrow from pyproject.toml
RUN pip install --no-cache-dir .

# Expose the dashboard port
EXPOSE 8000

# Metadata
ENV NAME="LocalAgent"
ENV VERSION="0.1.0"
ENV LOCAL_AGENT_VAULT="/app/vaults"

# Entry point: Start the unified dashboard and security broker
CMD ["local-agent", "serve", "--host", "0.0.0.0", "--port", "8000"]
