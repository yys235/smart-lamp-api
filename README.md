# Smart Lamp API

Python FastAPI implementation of the Smart Lamp control service.

## Features

- REST API for controlling smart lamps
- UDP gateway discovery (port 41328)
- TCP communication with Ledo protocol (port 41330)
- SQLite database for operation logging
- Automatic log rotation and cleanup
- Event-driven architecture
- OpenAPI documentation

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Run

```bash
# Development
python -m app.main

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

Environment variables can be set in `.env` file:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# API Security
API_KEY=your-api-key

# UDP/TCP
UDP_PORT=41328
TCP_PORT=41330

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
LOG_ROTATION=10 MB
LOG_RETENTION=7 days

# Database
DATABASE_URL=sqlite+aiosqlite:///./smartlamp.db
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/health | Health check |
| GET | /api/v1/lamps | Get all lamps |
| GET | /api/v1/lamps/{id} | Get lamp by ID |
| POST | /api/v1/lamps/{id}/on | Turn on lamp |
| POST | /api/v1/lamps/{id}/off | Turn off lamp |
| POST | /api/v1/lamps/all/on | Turn on all lamps |
| POST | /api/v1/lamps/all/off | Turn off all lamps |
| PUT | /api/v1/lamps/{id}/color | Set lamp color |
| PUT | /api/v1/lamps/{id}/intensity | Set lamp intensity |
| GET | /api/v1/gateway/status | Gateway status |
| POST | /api/v1/gateway/discover | Discover gateway |
| POST | /api/v1/gateway/refresh | Refresh lamp list |
| GET | /api/v1/logs/status | Log disk usage |
| POST | /api/v1/logs/cleanup | Trigger log cleanup |

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Protocol

The API uses the Ledo binary protocol:
- Magic bytes: `0xF3 0xD4`
- Little-endian byte ordering
- 10-byte header + variable body

## License

MIT
