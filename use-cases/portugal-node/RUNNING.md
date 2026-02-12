# Running the TEF Synthetic Data Pipeline

Step-by-step instructions for running the TEF pipeline with both integration approaches.

## Prerequisites

- Docker and Docker Compose installed
- Orchestrator running (see `orchestrator/` directory)
- Ports available: 8001-8003 (TEF services), 18000 (orchestrator), 18101-18103 (sidecar adapters)

## Initial Setup

The TEF services (Data Provision, Knowledge Store, Synthetic Data) are provided by the Portugal node and are not included in this repository.

### Step 1: Obtain TEF Services

Contact the Portugal node team to obtain:
- `data_provision/` - Data loading and SQL query service
- `knowledge_store/` - Feature engineering service
- `synthetic_data_generation/` - DoppelGANger model training and generation

### Step 2: Create Directory Structure

```bash
mkdir -p use-cases-platform/tef-integrated
mkdir -p use-cases-platform/tef-sidecar
```

### Step 3: Set Up Integrated Approach

```bash
# Copy TEF services
cp -r <path-to-tef-services>/data_provision use-cases-platform/tef-integrated/
cp -r <path-to-tef-services>/knowledge_store use-cases-platform/tef-integrated/
cp -r <path-to-tef-services>/synthetic_data_generation use-cases-platform/tef-integrated/

# Copy common module
cp -r use-cases/portugal-node/common use-cases-platform/tef-integrated/

# Copy configuration files
cp use-cases/portugal-node/blueprint.json use-cases-platform/tef-integrated/
cp use-cases/portugal-node/dockerinfo-integrated.json use-cases-platform/tef-integrated/dockerinfo.json
cp use-cases/portugal-node/docker-compose-all.yml use-cases-platform/tef-integrated/
```

Modify each TEF service's Dockerfile to copy the common module. Add this line before the CMD instruction:

```dockerfile
COPY common/ ./common/
```

For Python 3.9 services (synthetic_data_generation), also add `eval_type_backport` to the pip install:
```dockerfile
RUN pip install --no-cache-dir httpx eval_type_backport
```

Then add the following to each TEF service's `main.py` after the FastAPI app is created:

```python
# --- AI-Effect Control Interface ---
try:
    from common import create_control_router, data_provision_handlers

    app.include_router(
        create_control_router(data_provision_handlers),
        prefix="/control",
    )
except ImportError as e:
    import logging
    logging.warning(f"AI-Effect control interface not available: {e}")
```

Use the appropriate handler import for each service:
- `data_provision/main.py`: `from common import create_control_router, data_provision_handlers`
- `knowledge_store/src/main.py`: `from common import create_control_router, knowledge_store_handlers`
- `synthetic_data_generation/main.py`: `from common import create_control_router, synthetic_data_handlers`

### Step 4: Set Up Sidecar Approach

```bash
# Copy common module and sidecar adapters
cp -r use-cases/portugal-node/common use-cases-platform/tef-sidecar/
cp -r use-cases/portugal-node/sidecar-adapters use-cases-platform/tef-sidecar/

# Copy configuration files
cp use-cases/portugal-node/blueprint.json use-cases-platform/tef-sidecar/
cp use-cases/portugal-node/dockerinfo-sidecar.json use-cases-platform/tef-sidecar/dockerinfo.json

# Set up data file directory for sidecar volume mount
mkdir -p use-cases-platform/tef-sidecar/synthetic_data_generation
cp <path-to-data>/real_data.csv use-cases-platform/tef-sidecar/synthetic_data_generation/
```

### Step 5: Prepare Test Data

Ensure a CSV data file exists for testing. The default configuration expects `/app/real_data.csv` inside containers. Update volume mounts in docker-compose files as needed.

## Option 1: Integrated Adapters

### Step 1: Start TEF Services

```bash
cd use-cases-platform/tef-integrated
docker compose -f docker-compose-all.yml up -d --build
```

Verify services:
```bash
docker ps --filter "name=tef-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected:
```
NAMES                STATUS         PORTS
tef-synthetic-data   Up X minutes   0.0.0.0:8003->600/tcp
tef-knowledge-store  Up X minutes   0.0.0.0:8002->8000/tcp
tef-data-provision   Up X minutes   0.0.0.0:8001->600/tcp
tef-clickhouse       Up X minutes   0.0.0.0:8123->8123/tcp
```

### Step 2: Start Orchestrator

```bash
cd orchestrator
docker compose up -d
```

Workers automatically join the `ai-effect-services` network.

### Step 3: Submit Workflow

```bash
cd use-cases-platform/tef-integrated

curl -s -X POST http://localhost:18000/workflows \
  -H "Content-Type: application/json" \
  -d "{
  \"blueprint\": $(cat blueprint.json),
  \"dockerinfo\": $(cat dockerinfo.json),
  \"inputs\": [{
    \"protocol\": \"inline\",
    \"uri\": \"$(echo '{\"file_path\": \"/app/real_data.csv\", \"max_rows\": 200, \"rename_columns\": {\"datetime\": \"timestamp\"}}' | base64 -w0)\",
    \"format\": \"json\"
  }]
}"
```

### Step 4: Monitor Workflow

```bash
# Check workflow status
curl -s http://localhost:18000/workflows/<workflow_id> | jq .

# Check task status
curl -s http://localhost:18000/workflows/<workflow_id>/tasks | jq '.tasks[] | {node_key, status, error}'
```

Expected progression:
1. `data_loader:LoadData` - completed
2. `feature_engineer:ApplyFeatures` - completed
3. `model_trainer:TrainModel` - running, then completed
4. `data_generator:GenerateData` - completed

### Step 5: Verify Results

```bash
# Get GenerateData task_id
TASK_ID=$(curl -s http://localhost:18000/workflows/<workflow_id>/tasks | jq -r '.tasks[] | select(.node_key == "data_generator:GenerateData") | .task_id')

# Fetch generated data
curl -s "http://localhost:8003/control/data/$TASK_ID" | head -5
```

## Option 2: Sidecar Adapters

### Step 1: Start TEF Services

```bash
cd use-cases-platform/tef-integrated
docker compose -f docker-compose-all.yml up -d --build
```

### Step 2: Start Sidecar Adapters

```bash
cd use-cases-platform/tef-sidecar/sidecar-adapters
docker compose up -d --build
```

Verify adapters:
```bash
docker ps --filter "name=sidecar" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Step 3: Start Orchestrator

```bash
cd orchestrator
docker compose up -d
```

### Step 4: Verify Health

```bash
curl -s http://localhost:18103/health
curl -s http://localhost:18101/health
curl -s http://localhost:18102/health
```

All should return `{"status":"ok"}`.

### Step 5: Submit Workflow

```bash
cd use-cases-platform/tef-sidecar

curl -s -X POST http://localhost:18000/workflows \
  -H "Content-Type: application/json" \
  -d "{
  \"blueprint\": $(cat blueprint.json),
  \"dockerinfo\": $(cat dockerinfo.json),
  \"inputs\": [{
    \"protocol\": \"inline\",
    \"uri\": \"$(echo '{\"file_path\": \"/app/real_data.csv\", \"max_rows\": 200, \"rename_columns\": {\"datetime\": \"timestamp\"}}' | base64 -w0)\",
    \"format\": \"json\"
  }]
}"
```

### Step 6: Verify Results

```bash
# Fetch from sidecar adapter
curl -s "http://localhost:18102/control/data/$TASK_ID" | head -5
```

## Troubleshooting

### Code Changes Not Reflected in Container

Docker caches build layers. When modifying Python code that is copied into images:

```bash
# Force rebuild without cache
docker compose -f docker-compose-all.yml build --no-cache <service-name>

# Recreate container with new image
docker compose -f docker-compose-all.yml up -d --force-recreate <service-name>
```

For iterative development, rebuild only the affected service rather than all services.

### HTTP 404 on /control/execute

Verify the endpoint path is correct:
```bash
curl -s http://localhost:8001/openapi.json | jq '.paths | keys'
```

If endpoints show `/control/control/execute` (doubled prefix), the router prefix is applied twice. The `create_control_router()` function returns a router without prefix. When using the integrated approach, add the prefix when including the router:

```python
app.include_router(create_control_router(handlers), prefix="/control")
```

### Container Crash Loop (Python 3.9 Type Hints)

If a container fails with `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'`:

The `str | None` syntax requires Python 3.10+. The common module includes `from __future__ import annotations` for compatibility, but Pydantic still evaluates type hints at runtime.

Solution: Install `eval_type_backport` in the container:
```dockerfile
RUN pip install eval_type_backport
```

### Network Connectivity Issues

Verify containers are on the shared network:
```bash
docker network inspect ai-effect-services --format '{{range .Containers}}{{.Name}} {{end}}'
```

Expected containers: tef-clickhouse, tef-data-provision, tef-knowledge-store, tef-synthetic-data, orchestrator-worker-1, orchestrator-worker-2, orchestrator-worker-3 (and sidecar adapters if using that approach).

If orchestrator workers are missing, ensure the orchestrator docker-compose includes:
```yaml
networks:
  services:
    name: ai-effect-services
    external: true
```

### Training Task Stuck in Running State

The training polling logic checks for completion via the `/training_info` endpoint response. If the response format differs from expected, the task may not complete.

Check training status directly:
```bash
curl -s "http://localhost:8003/training_info?username=demo_user&model_name=<model_name>" | jq .
```

The polling logic checks for: `trained: true`, `status: "completed"`, or `epoch >= total_epochs`.

### File Not Found in Sidecar Container

Sidecar adapters run in separate containers and do not have access to files in TEF service containers. Mount required data files in the sidecar docker-compose:

```yaml
volumes:
  - ./path/to/data.csv:/app/real_data.csv:ro
```

### Connection Refused from Orchestrator

1. Verify the service is running: `docker ps`
2. Check dockerinfo.json uses correct hostnames (container names for Docker networking)
3. Verify port mappings match between docker-compose and dockerinfo.json

### Common Errors Reference

| Error | Cause | Resolution |
|-------|-------|------------|
| `No such file or directory` | Data file not mounted | Add volume mount in docker-compose |
| `Connection refused` | Service not running or wrong port | Verify `docker ps` and port mappings |
| `HTTP 404` | Wrong endpoint path | Check `/openapi.json` for available paths |
| `HTTP 405` | Wrong HTTP method | Ensure POST for `/execute`, GET for others |
| `timestamp column not found` | Column rename not applied | Verify `rename_columns` in input parameters |

### Viewing Service Logs

```bash
# TEF services
docker logs tef-data-provision --tail 50
docker logs tef-knowledge-store --tail 50
docker logs tef-synthetic-data --tail 50

# Sidecar adapters
docker logs sidecar-adapters-data-provision-adapter-1 --tail 50
docker logs sidecar-adapters-knowledge-store-adapter-1 --tail 50
docker logs sidecar-adapters-synthetic-data-adapter-1 --tail 50

# Orchestrator
docker logs orchestrator-worker-1 --tail 50
```

## Cleanup

```bash
# Stop sidecar adapters
cd use-cases-platform/tef-sidecar/sidecar-adapters
docker compose down

# Stop TEF services
cd use-cases-platform/tef-integrated
docker compose -f docker-compose-all.yml down

# Stop orchestrator
cd orchestrator
docker compose down

# Remove volumes (deletes trained models)
docker volume rm tef-clickhouse-data tef-synthetic-models
```
