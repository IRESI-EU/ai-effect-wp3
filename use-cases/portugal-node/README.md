# TEF Synthetic Data Pipeline Integration

This directory contains two integration approaches for connecting TEF services to the AI-Effect orchestrator.

## Language and Stack Agnostic

The AI-Effect Control Interface is entirely HTTP-based. While this implementation uses Python/FastAPI (matching the TEF services stack), adapters can be implemented in any language or framework.

Requirements:
- Expose standard HTTP REST endpoints
- Accept and return JSON payloads
- Serve data files via HTTP when using URL references

The orchestrator communicates purely via HTTP calls and has no knowledge of the implementation language.

## Prerequisites

- Docker and Docker Compose
- TEF services (Data Provision, Knowledge Store, Synthetic Data)
- Python 3.10+ (Python 3.9 supported with compatibility shims)

## Directory Structure

```
portugal-node/
├── common/                        # Shared modules
│   ├── __init__.py
│   ├── task_manager.py            # Thread-safe task state manager
│   ├── control_interface.py       # FastAPI control endpoints
│   └── tef_operations.py          # TEF operation handlers
├── integrated-adapters/           # For embedding in TEF services
│   ├── control_router.py
│   ├── data_provision_adapter.py
│   ├── knowledge_store_adapter.py
│   └── synthetic_data_adapter.py
├── sidecar-adapters/              # Standalone adapter services
│   ├── docker-compose.yml
│   ├── data_provision/
│   ├── knowledge_store/
│   └── synthetic_data/
├── blueprint.json
├── dockerinfo-integrated.json
└── dockerinfo-sidecar.json
```

## Integration Approaches

### Option 1: Integrated Adapters

Embed adapter modules directly in existing FastAPI applications.

```python
from fastapi import FastAPI
from common import create_control_router, data_provision_handlers

app = FastAPI()

# Add control interface with /control prefix
app.include_router(
    create_control_router(data_provision_handlers),
    prefix="/control"
)
```

When to use:
- Minimal additional infrastructure required
- Services are already FastAPI applications
- Direct integration preferred over network hops

### Option 2: Sidecar Adapters

Standalone adapter services that run alongside TEF services.

```bash
cd sidecar-adapters
docker compose up -d --build
```

Adapter ports:

| Adapter | Port | TEF Service |
|---------|------|-------------|
| data-provision-adapter | 18103 | Data Provision (8001) |
| knowledge-store-adapter | 18101 | Knowledge Store (8002) |
| synthetic-data-adapter | 18102 | Synthetic Data (8003) |

When to use:
- Cannot modify TEF service code
- Isolation between AI-Effect interface and business logic required
- Containerized deployment preferred

## Common Module

The `common/` directory contains shared code used by both approaches.

### task_manager.py

Thread-safe task state manager for tracking async operations and storing data for HTTP serving.

```python
from common import get_task_manager

tm = get_task_manager()
tm.register(task_id, status="running")
tm.update_progress(task_id, 50)
tm.complete(task_id, output)
tm.store_data(task_id, csv_data, "csv")
```

### control_interface.py

FastAPI control endpoints and application creation.

```python
from common import create_control_router, create_app, run

# Integrated: add router to existing app
router = create_control_router(execute_handlers)
app.include_router(router, prefix="/control")

# Sidecar: create standalone app
app = create_app(execute_handlers, "Service Name")

# Or run directly
run(execute_handlers, "Service Name")
```

### tef_operations.py

Pre-built TEF operation handlers:

| Handler | Description |
|---------|-------------|
| `execute_LoadData` | Load data from CSV file |
| `execute_QueryDatabase` | Query ClickHouse via Data Provision |
| `execute_ApplyFeatures` | Apply features via Knowledge Store |
| `execute_TrainModel` | Train model via Synthetic Data (async) |
| `execute_GenerateData` | Generate synthetic data |

Handler exports by service:
- `data_provision_handlers`: LoadData, QueryDatabase
- `knowledge_store_handlers`: ApplyFeatures
- `synthetic_data_handlers`: TrainModel, GenerateData

## Configuration Files

### blueprint.json

Defines the pipeline topology:
```
data_loader -> feature_engineer -> model_trainer -> data_generator
```

### dockerinfo-*.json

Service endpoint mappings:
- `dockerinfo-integrated.json`: TEF services directly (ports 8001-8003)
- `dockerinfo-sidecar.json`: Sidecar adapters (ports 18101-18103)

### Environment Variables

Required environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SELF_URL` | Service URL for HTTP references | `http://my-service:8080` |
| `DATA_PROVISION_URL` | Data Provision service URL | `http://data-provision:600` |
| `KNOWLEDGE_STORE_URL` | Knowledge Store service URL | `http://knowledge-store:8000` |
| `SYNTHETIC_DATA_URL` | Synthetic Data service URL | `http://synthetic-data:600` |

Use container names for Docker network communication, not `localhost`.

## Control Interface

All adapters expose the standard AI-Effect control interface:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/control/execute` | POST | Start an operation |
| `/control/status/{task_id}` | GET | Check task status |
| `/control/output/{task_id}` | GET | Retrieve task output |
| `/control/data/{task_id}` | GET | Serve raw data |
| `/health` | GET | Health check |

### Data Passing via HTTP URLs

Services store output data and return HTTP URL references:

```json
{
  "protocol": "http",
  "uri": "http://service:port/control/data/{task_id}",
  "format": "csv"
}
```

Downstream services fetch data directly from the URL.

## Python Version Compatibility

The common module uses `from __future__ import annotations` for Python 3.9 compatibility. The synthetic_data_generation service requires Python 3.9 due to dependency constraints (gretel-synthetics). Other services can use Python 3.10+.

For Python 3.9 environments, ensure `eval_type_backport` is installed for Pydantic type hint evaluation.

## Running the Pipeline

See `RUNNING.md` for step-by-step instructions.

## TEF Service Documentation

Once running:
- Data Provision: http://localhost:8001/docs
- Knowledge Store: http://localhost:8002/docs
- Synthetic Data: http://localhost:8003/docs
