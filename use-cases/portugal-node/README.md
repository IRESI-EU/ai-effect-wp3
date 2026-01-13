# TEF Synthetic Data Pipeline Integration

This directory contains two integration approaches for connecting TEF services to the AI-Effect orchestrator.

## Language & Stack Agnostic

**Important**: The AI-Effect Control Interface is entirely HTTP-based. While this example uses **Python/FastAPI** (matching the TEF services stack), adapters can be implemented in **any language or framework** - Node.js, Java, Go, Rust, C#, etc.

The only requirements are:
- Expose standard HTTP REST endpoints
- Accept and return JSON payloads
- Serve data files via HTTP when using URL references

The orchestrator communicates purely via HTTP calls and has no knowledge of what language runs behind the endpoints.

## Prerequisites

- TEF services running (Data Provision, Knowledge Store, Synthetic Data)
- Python 3.12+
- Docker (for sidecar approach)

## Directory Structure

```
portugal-node/
├── common/                        # Shared modules (use these)
│   ├── __init__.py
│   ├── task_manager.py            # Thread-safe task state manager
│   ├── control_interface.py       # FastAPI control endpoints
│   └── tef_operations.py          # TEF operation handlers
├── integrated-adapters/           # For embedding in TEF services
│   ├── control_router.py          # Re-exports from common
│   ├── data_provision_adapter.py
│   ├── knowledge_store_adapter.py
│   └── synthetic_data_adapter.py
├── sidecar-adapters/              # Standalone adapter services
│   ├── handler.py                 # Re-exports from common
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

Partners include adapter modules directly in their existing FastAPI applications.

**Integration example:**
```python
from fastapi import FastAPI
from common import create_control_router, data_provision_handlers

app = FastAPI()

# Add control interface with TEF operation handlers
app.include_router(create_control_router(data_provision_handlers))
```

Or import individual handlers to customize:
```python
from common import (
    create_control_router,
    execute_LoadData,
    execute_QueryDatabase,
)

app.include_router(create_control_router({
    "LoadData": execute_LoadData,
    "QueryDatabase": execute_QueryDatabase,
}))
```

**When to use:**
- You want minimal additional infrastructure
- Your services are already FastAPI applications
- You prefer direct integration over network hops

### Option 2: Sidecar Adapters

Standalone adapter services that run alongside TEF services and forward requests.

**Deployment:**
```bash
cd sidecar-adapters
docker compose up -d
```

**Services exposed:**
| Adapter | Port | TEF Service |
|---------|------|-------------|
| data-provision-adapter | 18103 | Data Provision (8001) |
| knowledge-store-adapter | 18101 | Knowledge Store (8002) |
| synthetic-data-adapter | 18102 | Synthetic Data (8003) |

**When to use:**
- You cannot modify TEF service code
- You want isolation between AI-Effect interface and business logic
- You prefer containerized deployment

## Common Module

The `common/` directory contains all shared code:

### task_manager.py

Thread-safe task state manager. Tracks async task state and stores raw data for HTTP serving.

```python
from common import get_task_manager

tm = get_task_manager()

# Register a task
tm.register(task_id, status="running")

# Update progress from background thread
tm.update_progress(task_id, 50)

# Complete or fail
tm.complete(task_id, output)
tm.fail(task_id, "Error message")

# Query state
status = tm.get_status(task_id)
output = tm.get_output(task_id)

# Store and retrieve raw data for HTTP URL references
tm.store_data(task_id, csv_data, "csv")
data, format = tm.get_data(task_id)
```

### control_interface.py

FastAPI control endpoints and app creation.

```python
from common import create_control_router, create_app, run

# For integrated approach - add router to existing app
router = create_control_router(execute_handlers)
app.include_router(router)

# For sidecar approach - create standalone app
app = create_app(execute_handlers, "Service Name")

# Or run directly
run(execute_handlers, "Service Name")
```

### tef_operations.py

Pre-built TEF operation handlers:
- `execute_LoadData` - Load data from file
- `execute_QueryDatabase` - Query ClickHouse via Data Provision
- `execute_ApplyFeatures` - Apply features via Knowledge Store
- `execute_TrainModel` - Train model via Synthetic Data (async)
- `execute_GenerateData` - Generate data via Synthetic Data

Handler exports by service:
- `data_provision_handlers` - LoadData, QueryDatabase
- `knowledge_store_handlers` - ApplyFeatures
- `synthetic_data_handlers` - TrainModel, GenerateData

## Configuration Files

### blueprint.json

Defines the pipeline topology for the orchestrator:
```
data_loader -> feature_engineer -> model_trainer -> data_generator
```

### dockerinfo-*.json

Service endpoint mappings:
- `dockerinfo-integrated.json`: Points to TEF services directly (ports 8001-8003)
- `dockerinfo-sidecar.json`: Points to sidecar adapters (ports 18101-18103)

### Environment Variables

Each service needs `SELF_URL` to generate correct HTTP URL references:

```yaml
# docker-compose.yml
services:
  my-service:
    environment:
      - SELF_URL=http://my-service:8080  # Use container name for Docker networking
```

**Important**: Use container names (not `localhost` or `host.docker.internal`) for Docker network communication.

## Running the Pipeline

See `RUNNING.md` for detailed step-by-step instructions.

Quick start:
1. Start TEF services
2. Choose integration approach and deploy adapters
3. Connect orchestrator to TEF network
4. Submit workflow

## Control Interface

All adapters expose the standard AI-Effect control interface:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/control/execute` | POST | Start an operation |
| `/control/status/{task_id}` | GET | Check task status |
| `/control/output/{task_id}` | GET | Retrieve task output (DataReference) |
| `/control/data/{task_id}` | GET | Serve raw data for HTTP URL references |
| `/health` | GET | Health check |

### HTTP URL Reference Data Passing

Services store output data and return HTTP URLs:

```json
{
  "protocol": "http",
  "uri": "http://service:port/control/data/{task_id}",
  "format": "csv"
}
```

Downstream services fetch data directly from the URL. This approach:
- Avoids format conversion issues
- Reduces payload sizes
- Allows services to stream large datasets

## Operations

### LoadData
Loads data from CSV files.

**Parameters:**
- `file_path`: Path to CSV file
- `max_rows`: Maximum rows to load (default: 1000)
- `rename_columns`: Column rename mapping

### ApplyFeatures
Applies feature engineering functions.

**Parameters:**
- `function_name`: Feature function to apply (e.g., "DatetimeFeatures")
- `function_kwargs`: Function parameters

### TrainModel
Trains a synthetic data model (async operation).

**Parameters:**
- `username`: User ID
- `model_name`: Model name
- `index_col`: Index column name
- `epochs`: Training epochs
- `batch_size`: Batch size

### GenerateData
Generates synthetic data from trained model.

**Parameters:**
- `num_examples`: Number of samples to generate
- `output_format`: Output format (csv or json)

## TEF Services

Once running:
- Data Provision: http://localhost:8001/docs
- Knowledge Store: http://localhost:8002/docs
- Synthetic Data: http://localhost:8003/docs

## Known Issues

**Hour feature handling**

The DatetimeFeatures function returns hour as integers 0-23. The DoppelGANger model detects these as numeric and treats them as continuous variables, generating invalid values like 9.34 or 11.87 instead of proper hours.

Fix: Convert hour values to categorical strings (hour_0, hour_1, etc.) before training. This forces the model to treat them as discrete categories.

**Column naming**

Knowledge Store requires "timestamp" column while Synthetic Data defaults to "datetime". The Synthetic Data service has an index_col parameter that lets you specify which column to use:

```bash
curl -X POST "http://localhost:8003/train?index_col=timestamp..." \
  -F "uploaded_file=@data.csv"
```
