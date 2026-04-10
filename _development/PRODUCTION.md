# Local Agent v4.0 - Production Deployment Guide

## Prerequisites

### Hardware Requirements

| Deployment Size | CPU | RAM | Storage | GPU |
|-----------------|-----|-----|---------|-----|
| **Small (1-10 users)** | 4 cores | 8GB | 20GB | Optional |
| **Medium (10-50 users)** | 8 cores | 16GB | 50GB | 8GB VRAM |
| **Large (50-200 users)** | 16 cores | 32GB | 100GB | 16GB VRAM |

### Software Requirements

- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL)
- Ollama (auto-installed by desktop app)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/local-agent-v4
cd local-agent-v4
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Production Server
```bash
# Windows
.\run_prod.ps1 -WithPostgres

# Linux/macOS
./run_prod.sh --with-postgres
```

### 4. Access Application
- Web UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment Options

### Option 1: Single Server (Small/Medium)

```bash
# Start with SQLite (development)
python -m local_agent.web.app

# Start with PostgreSQL (production)
export DB_TYPE=postgres
export DATABASE_URL="postgresql://user:pass@localhost/local_agent"
python -m local_agent.web.app
```

### Option 2: Docker Compose

```bash
docker-compose -f docker-compose.postgres.yml up -d
docker-compose up -d
```

### Option 3: Kubernetes (Enterprise)

```bash
helm install local-agent ./k8s/helm/
```

## Security Checklist

- [ ] Generate secure API key: `openssl rand -hex 32`
- [ ] Generate JWT secret: `openssl rand -hex 32`
- [ ] Generate audit encryption key: `openssl rand -hex 32`
- [ ] Set `AGENT_API_KEY` in `.env`
- [ ] Configure `ALLOWED_ORIGINS` for production domain
- [ ] Enable HTTPS with reverse proxy (nginx/Caddy)
- [ ] Set up regular database backups

## Monitoring

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Metrics
```bash
curl http://localhost:8000/api/enterprise/analytics/usage
```

### Logs
```bash
# WebSocket log stream
wscat -c ws://localhost:8000/ws/logs?api_key=YOUR_KEY
```

## Backup & Recovery

### Manual Backup
```bash
python -c "from local_agent.core.db import db_manager; db_manager.backup()"
```

### Scheduled Backup (cron)
```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/local-agent-v4 && python -c "from local_agent.core.db import db_manager; db_manager.backup()"
```

## Troubleshooting

### Database Connection Issues
```bash
# Test PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check SQLite permissions
ls -la data/local_agent.db
```

### Ollama Not Responding
```bash
# Restart Ollama
ollama serve &
ollama pull phi3:mini
```

### WebSocket Connection Drops
- Verify API key in WebSocket URL
- Check CORS configuration
- Ensure `ALLOWED_ORIGINS` includes your domain

## Support

- Documentation: https://docs.local-agent.com
- GitHub Issues: https://github.com/yourusername/local-agent-v4/issues
- Enterprise Support: support@local-agent.com
