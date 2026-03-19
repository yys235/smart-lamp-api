# Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Docker Commands](#docker-commands)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- (Optional) Make for convenience commands

---

## Local Development

### Quick Start

```bash
# Clone repository
git clone https://github.com/yys235/smart-lamp-api.git
cd smart-lamp-api

# Copy environment file
cp .env.example .env

# Start development server with hot reload
docker-compose --profile dev up
```

The API will be available at `http://localhost:8001`

### Manual Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Production Deployment

### Using Docker Compose

```bash
# Build and start production containers
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Using Docker Directly

```bash
# Build image
docker build -t smartlamp-api:latest .

# Run container
docker run -d \
  --name smartlamp-api \
  -p 8000:8000 \
  -p 41328:41328/udp \
  -p 41330:41330 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  smartlamp-api:latest
```

### Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 8000 | TCP | HTTP API |
| 41328 | UDP | Gateway Discovery |
| 41330 | TCP | Lamp Control |

---

## Docker Commands

### Using Makefile

```bash
make build    # Build development image
make dev      # Run development server
make up       # Start production containers
make down     # Stop containers
make logs     # View logs
make shell    # Open shell in container
make test     # Run tests
```

### Manual Docker Commands

```bash
# Build image
docker build -t smartlamp-api:latest .

# View running containers
docker ps

# View logs
docker logs -f smartlamp-api

# Execute command in container
docker exec -it smartlamp-api bash

# Stop and remove container
docker stop smartlamp-api
docker rm smartlamp-api
```

---

## Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# API Security
API_KEY=your-secure-api-key-here

# UDP Configuration
UDP_PORT=41328
UDP_BUFFER_SIZE=2048

# TCP Configuration
TCP_PORT=41330
TCP_TIMEOUT=5
TCP_CONNECT_TIMEOUT=5

# Gateway
GATEWAY_DISCOVERY_TIMEOUT=30

# Retry
MAX_RETRIES=3
RETRY_DELAY=1.0

# Logging
LOG_LEVEL=INFO
```

---

## Health Checks

### Docker Health Check

The container includes a built-in health check:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Manual Health Check

```bash
# HTTP health endpoint
curl http://localhost:8000/health

# Expected response
{"status":"healthy","timestamp":"2025-03-19T10:00:00Z"}
```

### Kubernetes Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 20
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs smartlamp-api

# Common issues:
# - Port already in use: Change PORT in .env
# - Permission denied: Ensure logs/ and data/ directories exist
```

### Can't Access UDP/TCP Ports

```bash
# Check firewall rules
sudo ufw status

# Allow ports if needed
sudo ufw allow 41328/udp
sudo ufw allow 41330/tcp
```

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
rm -f data/smartlamp.db
docker-compose restart
```

### View Container Resource Usage

```bash
docker stats smartlamp-api
```

---

## Production Considerations

### Security

1. Change default `API_KEY` in production
2. Use `DEBUG=false` in production
3. Run containers as non-root user (configured by default)
4. Use HTTPS/TLS reverse proxy (nginx, traefik)

### Persistence

- Logs: Mounted to `./logs`
- Database: Mounted to `./data`

### Scaling

For horizontal scaling, consider:
- External database (PostgreSQL)
- Shared storage for logs
- Load balancer (nginx, HAProxy)

### Monitoring

Recommended integrations:
- Prometheus metrics
- Grafana dashboards
- Log aggregation (ELK, Loki)

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yys235/smart-lamp-api/issues
- Documentation: https://github.com/yys235/smart-lamp-api/blob/main/docs/
