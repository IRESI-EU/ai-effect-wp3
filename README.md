# AI-Effect Orchestrator Platform

A workflow orchestration platform for AI-Effect microservice pipelines. The orchestrator coordinates service execution via REST API and supports both gRPC (protobuf) and HTTP Control Interface communication patterns.

## Overview

The platform consists of:

- **Orchestrator** - REST API + worker processes that execute workflows
- **Service Templates** - Reference implementations for building compatible services
- **Use Cases** - Example pipelines and real-world integrations

## Project Structure

```
ai-effect-wp3/
├── orchestrator/                  # Workflow orchestrator
│   ├── src/
│   │   ├── api/                   # REST API (FastAPI)
│   │   ├── models/                # Data models
│   │   └── services/              # Core services
│   ├── docker-compose.yml         # Orchestrator deployment
│   └── tests/                     # Unit, integration, e2e tests
├── use-cases/
│   ├── templates/                 # Service templates
│   │   ├── file_based/            # HTTP control + file storage
│   │   └── protobuf_based/        # HTTP control + gRPC data
│   ├── file_based_energy_pipeline/    # Example pipeline
│   ├── protobuf_based_energy_pipeline/ # Example with gRPC
│   └── portugal-node/             # TEF third-party integration
├── scripts/                       # Build and generation tools
└── use-cases-platform/            # Generated deployment packages
```

## Quick Start

### 1. Start the Orchestrator

```bash
cd orchestrator
docker compose up -d
```

This starts:
- **Redis** - State management (port 16379)
- **API** - REST endpoint (port 18000)
- **Workers** - 3 worker replicas for task execution

### 2. Deploy Services

Services must implement the AI-Effect Control Interface:

```
POST /control/execute        - Execute an operation
GET  /control/status/{id}    - Check task status
GET  /control/output/{id}    - Get task output
GET  /health                 - Health check
```

### 3. Submit a Workflow

```bash
curl -X POST http://localhost:18000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": {...},
    "dockerinfo": {...},
    "inputs": [{"protocol": "inline", "uri": "...", "format": "json"}]
  }'
```

### 4. Monitor Progress

```bash
# Check workflow status
curl http://localhost:18000/workflows/{workflow_id}

# Check individual tasks
curl http://localhost:18000/workflows/{workflow_id}/tasks
```

## Architecture

### Orchestrator Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Orchestrator                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌─────────┐    ┌─────────────────────────┐  │
│  │   API   │───▶│  Redis  │◀───│   Workers (x3)          │  │
│  │  :8000  │    │  :6379  │    │   - Execute tasks       │  │
│  └─────────┘    └─────────┘    │   - Call services       │  │
│                                │   - Update state        │  │
│                                └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         Services                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │ Service A │  │ Service B │  │ Service C │               │
│  │  :8080    │  │  :8080    │  │  :8080    │               │
│  └───────────┘  └───────────┘  └───────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### Communication Patterns

**HTTP Control Interface** (all services):
- Orchestrator communicates with services via HTTP
- Standard endpoints: `/control/execute`, `/control/status`, `/control/output`

**Data Exchange** (service-to-service):
- **HTTP URLs** - Services return URLs to data, downstream services fetch directly
- **gRPC** - Services expose gRPC endpoints for direct data transfer
- **Inline** - Small data embedded as base64 in responses

## Service Templates

Templates for building AI-Effect compatible services:

| Template | Location | Use Case |
|----------|----------|----------|
| File Sequential | `use-cases/templates/file_based/sequential/` | Quick ops, shared storage |
| File Concurrent | `use-cases/templates/file_based/concurrent/` | Long-running, shared storage |
| Protobuf Sequential | `use-cases/templates/protobuf_based/sequential/` | Quick ops, gRPC data |
| Protobuf Concurrent | `use-cases/templates/protobuf_based/concurrent/` | Long-running, gRPC data |

See `use-cases/templates/README.md` for detailed documentation.

## Use Cases

### file_based_energy_pipeline

Simple three-service pipeline demonstrating file-based data exchange:

```
data_generator → data_analyzer → report_generator
```

### protobuf_based_energy_pipeline

Same pipeline with gRPC data exchange between services.

### portugal-node (TEF Integration)

Real-world integration with third-party TEF services for synthetic data generation:

```
LoadData → ApplyFeatures → TrainModel → GenerateData
```

Demonstrates:
- **Integrated adapters** - Embed control interface in existing services
- **Sidecar adapters** - Separate adapter containers alongside services
- **HTTP URL reference** - Data passing via HTTP endpoints

See `use-cases/portugal-node/README.md` for details.

## Configuration Files

### blueprint.json

Defines workflow topology:

```json
{
  "pipeline_id": "my-pipeline",
  "name": "My Pipeline",
  "nodes": [...],
  "operation_signature_list": [...]
}
```

### dockerinfo.json

Service network configuration:

```json
{
  "docker_info_list": [
    {
      "container_name": "service_a",
      "ip_address": "service-a",
      "port": "8080"
    }
  ]
}
```

## API Reference

### Submit Workflow

```
POST /workflows
```

Request:
```json
{
  "blueprint": {...},
  "dockerinfo": {...},
  "inputs": [
    {"protocol": "inline", "uri": "<base64>", "format": "json"}
  ]
}
```

Response:
```json
{
  "workflow_id": "wf-abc123",
  "status": "running"
}
```

### Get Workflow Status

```
GET /workflows/{workflow_id}
```

### Get Workflow Tasks

```
GET /workflows/{workflow_id}/tasks
```

### Health Check

```
GET /health
```

## Development

### Prerequisites

- Docker and Docker Compose
- Python 3.12+

### Running Tests

```bash
cd orchestrator
pytest tests/
```

### Building Services

Use the scripts to generate deployment packages:

```bash
# Generate build script
python scripts/build-script-generator.py use-cases/my_pipeline

# Create platform export
python scripts/onboarding-export-generator.py \
  use-cases/my_pipeline \
  use-cases-platform/my_pipeline

# Generate docker-compose
python scripts/docker-compose-generator.py \
  use-cases-platform/my_pipeline
```

## Third-Party Integration

To integrate existing services with AI-Effect:

1. **Choose approach**: Integrated (embed) or Sidecar (separate container)
2. **Implement Control Interface**: `/control/execute`, `/control/status`, `/control/output`
3. **Handle data references**: Support HTTP/gRPC/inline protocols
4. **Configure networking**: Use Docker DNS for service discovery

See `use-cases/portugal-node/` for a complete example.

## License

Developed for AI-Effect consortium partners under project licensing agreements.
