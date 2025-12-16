# Service Templates

Reference implementations for building services that integrate with the AI-Effect orchestration platform.

## Templates

| Template | Directory | Use When |
|----------|-----------|----------|
| Sequential | `sequential/` | Operations complete quickly (< 30 sec) |
| Concurrent | `concurrent/` | Long-running operations with progress tracking |

## Structure

Each template contains:

```
<template>/
├── handler.py        # Orchestrator interface (don't modify)
├── service.py        # Your methods go here
├── Dockerfile
├── requirements.txt
└── README.md
```

## Control Interface

Services must respond to these HTTP endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/control/execute` | POST | Start task execution |
| `/control/status/{task_id}` | GET | Poll task status (concurrent only) |
| `/control/output/{task_id}` | GET | Get task output (concurrent only) |

## Sequential vs Concurrent

### Sequential

```
Orchestrator                    Service
     |                              |
     |--- POST /control/execute --->|
     |                              | (process: 1-30 sec)
     |<-- {status: "complete"} -----|
```

- Single request-response cycle
- No background processing
- Simpler implementation

### Concurrent

```
Orchestrator                    Service
     |                              |
     |--- POST /control/execute --->|
     |<-- {status: "running"} ------|
     |                              |
     |                    [background thread]
     |                              |
     |--- GET /control/status ----->|
     |<-- {progress: 50} -----------|
     |                              |
     |--- GET /control/status ----->|
     |<-- {status: "complete"} -----|
     |                              |
     |--- GET /control/output ----->|
     |<-- {output: {...}} ----------|
```

- Returns immediately, processes in background
- Progress tracking via polling
- Thread-safe task management

## Execute Request

```json
{
  "method": "ProcessData",
  "workflow_id": "wf-123",
  "task_id": "task-456",
  "inputs": [
    {"protocol": "s3", "uri": "s3://bucket/input.json", "format": "json"}
  ],
  "parameters": {"threshold": 0.5}
}
```

## DataReference

Data passed between tasks:

| Field | Description |
|-------|-------------|
| `protocol` | s3, http, https, nfs, inline |
| `uri` | Data location |
| `format` | json, csv, parquet, protobuf, binary |
