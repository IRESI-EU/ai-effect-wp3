# AI-Effect Orchestrator

REST API and worker processes for workflow orchestration.

## Quick Start

```bash
docker compose up -d
```

This starts:
- **redis** - State management (port 16379 externally, 6379 internally)
- **api** - REST API (port 18000 externally, 8000 internally)
- **worker** - 3 worker replicas for task execution

## Verify Running

```bash
# Check containers
docker compose ps

# Check health
curl http://localhost:18000/health
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/workflows` | POST | Submit workflow |
| `/workflows/{id}` | GET | Get workflow status |
| `/workflows/{id}/tasks` | GET | Get workflow tasks |

## Submit a Workflow

```bash
curl -X POST http://localhost:18000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {...},
    "dockerinfo": {...},
    "inputs": [{"protocol": "inline", "uri": "...", "format": "json"}]
  }'
```

## Connecting to Service Networks

When services run on a separate Docker network, connect the workers:

```bash
docker network connect <service-network> orchestrator-worker-1
docker network connect <service-network> orchestrator-worker-2
docker network connect <service-network> orchestrator-worker-3
```

## Logs

```bash
# All logs
docker compose logs -f

# API only
docker compose logs -f api

# Workers only
docker compose logs -f worker
```

## Stop

```bash
docker compose down
```

## Development

### Run Tests

```bash
# Unit tests
./run-tests-unit.sh

# Integration tests (requires Docker)
./run-tests-integration.sh

# All tests
./run-tests.sh
```

### Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis (required)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start API
REDIS_URL=redis://localhost:6379 python -m src.main

# Start worker (separate terminal)
REDIS_URL=redis://localhost:6379 python -m src.worker_daemon
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379` | Redis connection URL |
| `HOST` | `0.0.0.0` | API bind host |
| `PORT` | `8000` | API bind port |
| `WORKER_POLL_INTERVAL` | `1.0` | Worker task poll interval (seconds) |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Client   │────▶│     API     │────▶│    Redis    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                         ┌─────────────────────┼─────────────────────┐
                         │                     │                     │
                         ▼                     ▼                     ▼
                  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
                  │  Worker 1   │       │  Worker 2   │       │  Worker 3   │
                  └─────────────┘       └─────────────┘       └─────────────┘
                         │                     │                     │
                         └─────────────────────┼─────────────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Services   │
                                        └─────────────┘
```

- **API**: Receives workflow submissions, stores in Redis
- **Redis**: Workflow state, task queue, results
- **Workers**: Poll for tasks, execute by calling services, update state
