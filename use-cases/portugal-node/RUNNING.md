# Running the TEF Synthetic Data Pipeline

This guide provides step-by-step instructions for running the TEF pipeline with both integration approaches.

## Prerequisites

- Docker and Docker Compose installed
- Orchestrator running (see `orchestrator/` directory)
- Ports available: 8001-8003 (TEF services), 18000 (orchestrator), 18101-18103 (sidecar adapters)

---

## Initial Setup

The TEF services (Data Provision, Knowledge Store, Synthetic Data) are provided by the Portugal node and are **not included in this repository**. You need to obtain them separately and set up the directory structure.

### Step 1: Obtain TEF Services

Contact the Portugal node team or obtain the TEF services from their repository:
- `data_provision/` - Data loading and SQL query service
- `knowledge_store/` - Feature engineering service
- `synthetic_data_generation/` - DoppelGANger model training and generation

### Step 2: Create Directory Structure

Create the working directory structure in `use-cases-platform/` (this directory is gitignored):

```bash
mkdir -p use-cases-platform/tef-integrated
mkdir -p use-cases-platform/tef-sidecar
```

### Step 3: Set Up Integrated Approach

Copy TEF services and adapters for the integrated approach:

```bash
# Copy TEF services to tef-integrated/
cp -r <path-to-tef-services>/data_provision use-cases-platform/tef-integrated/
cp -r <path-to-tef-services>/knowledge_store use-cases-platform/tef-integrated/
cp -r <path-to-tef-services>/synthetic_data_generation use-cases-platform/tef-integrated/

# Copy common module and adapters from this directory
cp -r use-cases/portugal-node/common use-cases-platform/tef-integrated/
cp -r use-cases/portugal-node/integrated-adapters use-cases-platform/tef-integrated/

# Copy configuration files
cp use-cases/portugal-node/blueprint.json use-cases-platform/tef-integrated/
cp use-cases/portugal-node/dockerinfo-integrated.json use-cases-platform/tef-integrated/dockerinfo.json

# Copy docker-compose (you may need to adjust paths)
cp use-cases/portugal-node/docker-compose-all.yml use-cases-platform/tef-integrated/
```

Then integrate the adapters into each TEF service's main.py (see README.md for details).

### Step 4: Set Up Sidecar Approach

Copy TEF services and sidecar adapters:

```bash
# Copy TEF services (can reuse from tef-integrated or copy fresh)
# The sidecar approach uses the same TEF services

# Copy common module and sidecar adapters
cp -r use-cases/portugal-node/common use-cases-platform/tef-sidecar/
cp -r use-cases/portugal-node/sidecar-adapters use-cases-platform/tef-sidecar/

# Copy configuration files
cp use-cases/portugal-node/blueprint.json use-cases-platform/tef-sidecar/
cp use-cases/portugal-node/dockerinfo-sidecar.json use-cases-platform/tef-sidecar/dockerinfo.json
```

### Step 5: Prepare Test Data

Ensure you have a CSV data file for testing. The default configuration expects `/app/real_data.csv` inside the container. Update volume mounts in docker-compose files as needed.

---

## Option 1: Integrated Adapters

The integrated approach embeds adapters directly in the TEF service containers.

### Step 1: Start TEF Services

```bash
cd use-cases-platform/tef-integrated
docker compose -f docker-compose-all.yml up -d --build
```

Verify services are running:
```bash
docker ps --filter "name=tef-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
NAMES                STATUS         PORTS
tef-synthetic-data   Up X minutes   0.0.0.0:8003->600/tcp
tef-knowledge-store  Up X minutes   0.0.0.0:8002->8000/tcp
tef-data-provision   Up X minutes   0.0.0.0:8001->600/tcp
tef-clickhouse       Up X minutes   0.0.0.0:8123->8123/tcp, 0.0.0.0:9000->9000/tcp
```

### Step 2: Start the Orchestrator

```bash
cd orchestrator
docker compose up -d
```

### Step 3: Connect Orchestrator to TEF Network

```bash
docker network connect tef-network orchestrator-worker-1
docker network connect tef-network orchestrator-worker-2
docker network connect tef-network orchestrator-worker-3
```

### Step 4: Submit Workflow

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

Response:
```json
{
    "workflow_id": "wf-XXXXXXXXXXXX",
    "status": "running"
}
```

### Step 5: Monitor Workflow

Check workflow status (replace `wf-XXXX` with your workflow_id):
```bash
curl -s http://localhost:18000/workflows/wf-XXXX | python3 -m json.tool
```

Check individual tasks:
```bash
curl -s http://localhost:18000/workflows/wf-XXXX/tasks | python3 -m json.tool
```

Expected task progression:
1. `data_loader:LoadData` - completed
2. `feature_engineer:ApplyFeatures` - completed
3. `model_trainer:TrainModel` - running → completed (takes ~1-2 minutes)
4. `data_generator:GenerateData` - completed

### Step 6: Verify Results

Check generated synthetic data (get task_id from GenerateData task):
```bash
curl -s http://localhost:8003/control/data/{task_id} | head -10
```

Expected output (synthetic CSV data):
```
timestamp,RelativeHumidity_ref0_D0,Temperature_ref0_D0,...,hour,example
2020-09-20T00:00:00.000000+0000,86.340645,14.7193775,...,12.24938,1
...
```

---

## Option 2: Sidecar Adapters

The sidecar approach runs adapters as separate containers alongside TEF services.

### Step 1: Start TEF Services

First, start the base TEF services (same as integrated, but adapters will run separately):

```bash
cd use-cases-platform/tef-integrated
docker compose -f docker-compose-all.yml up -d --build
```

### Step 2: Start Sidecar Adapters

```bash
cd use-cases-platform/tef-sidecar/sidecar-adapters
docker compose up -d --build
```

Verify adapters are running:
```bash
docker ps --filter "name=sidecar" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
NAMES                                        STATUS       PORTS
sidecar-adapters-knowledge-store-adapter-1   Up X seconds 0.0.0.0:18101->8080/tcp
sidecar-adapters-synthetic-data-adapter-1    Up X seconds 0.0.0.0:18102->8080/tcp
sidecar-adapters-data-provision-adapter-1    Up X seconds 0.0.0.0:18103->8080/tcp
```

### Step 3: Start the Orchestrator

```bash
cd orchestrator
docker compose up -d
```

### Step 4: Connect Orchestrator to TEF Network

```bash
docker network connect tef-network orchestrator-worker-1
docker network connect tef-network orchestrator-worker-2
docker network connect tef-network orchestrator-worker-3
```

### Step 5: Verify Health

```bash
curl -s http://localhost:18103/health  # data-provision-adapter
curl -s http://localhost:18101/health  # knowledge-store-adapter
curl -s http://localhost:18102/health  # synthetic-data-adapter
```

All should return: `{"status":"ok"}`

### Step 6: Submit Workflow

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

### Step 7: Monitor Workflow

```bash
curl -s http://localhost:18000/workflows/wf-XXXX | python3 -m json.tool
curl -s http://localhost:18000/workflows/wf-XXXX/tasks | python3 -m json.tool
```

### Step 8: Verify Results

Check data at each stage:
```bash
# LoadData output
curl -s http://localhost:18103/control/data/{task_id} | head -3

# ApplyFeatures output
curl -s http://localhost:18101/control/data/{task_id} | head -3

# GenerateData output
curl -s http://localhost:18102/control/data/{task_id} | head -3
```

---

## Troubleshooting

### Network Connectivity Issues

If orchestrator can't reach services:
```bash
# Verify all containers are on tef-network
docker network inspect tef-network --format '{{range .Containers}}{{.Name}} {{end}}'

# Should list: tef-clickhouse, tef-data-provision, tef-knowledge-store, tef-synthetic-data,
#              orchestrator-worker-1, orchestrator-worker-2, orchestrator-worker-3
#              (and sidecar adapters if using that approach)
```

### Workflow Failed

Check task error:
```bash
curl -s http://localhost:18000/workflows/wf-XXXX/tasks | python3 -c "
import json, sys
for t in json.load(sys.stdin)['tasks']:
    if t['error']:
        print(f\"{t['node_key']}: {t['error']}\")
"
```

Check service logs:
```bash
# Integrated approach
docker logs tef-data-provision --tail 50
docker logs tef-knowledge-store --tail 50
docker logs tef-synthetic-data --tail 50

# Sidecar approach
docker logs sidecar-adapters-data-provision-adapter-1 --tail 50
docker logs sidecar-adapters-knowledge-store-adapter-1 --tail 50
docker logs sidecar-adapters-synthetic-data-adapter-1 --tail 50
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `No such file or directory: '/app/real_data.csv'` | Data file not mounted | Check volume mounts in docker-compose |
| `timestamp column not found` | Column rename failed | Verify `rename_columns` in input params |
| `datetime_col timestamp not found in train_df` | Wrong data format | Ensure ApplyFeatures returns CSV, not JSON |
| `Connection refused` | Service not running | Check `docker ps` and restart services |

---

## Cleanup

Stop all services:
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
```

Remove volumes (deletes trained models and data):
```bash
docker volume rm tef-clickhouse-data tef-synthetic-models
```
