# Sequential Protobuf Service Template

For operations that complete quickly (< 30 seconds) with direct gRPC data exchange between services.

## Architecture

```
Orchestrator                     Services
────────────                     ────────
     │
     │ HTTP /control/execute
     ├─────────────────────────► Service A
     │                              │
     │                              │ gRPC (data)
     │                              ▼
     │ HTTP /control/execute     Service B
     ├─────────────────────────► (fetches from A via gRPC)
     │                              │
     │                              │ gRPC (data)
     │                              ▼
     │ HTTP /control/execute     Service C
     └─────────────────────────► (fetches from B via gRPC)
```

- **Orchestrator** controls execution ORDER via HTTP
- **Services** exchange DATA directly via gRPC/protobuf

## Quick Start

```bash
pip install -r requirements.txt
python service.py
```

## How It Works

1. Service exposes two interfaces:
   - **HTTP** (port 8080): Control interface for orchestrator
   - **gRPC** (port 50051): Data interface for service-to-service communication

2. When orchestrator triggers execution:
   - Service fetches input from upstream via gRPC
   - Processes the data
   - Caches result for downstream services
   - Returns gRPC endpoint reference to orchestrator

3. Orchestrator passes the gRPC reference to downstream services

## Adding Methods

Edit `service.py`:

```python
def execute_MyMethod(request: ExecuteRequest) -> ExecuteResponse:
    # 1. Fetch input from upstream via gRPC
    for inp in request.inputs:
        if inp.get("protocol") == "grpc":
            upstream_data = fetch_from_upstream(inp["uri"])

    # 2. Process data
    result = process(upstream_data)

    # 3. Cache for downstream
    with _result_lock:
        _last_result = result

    # 4. Return gRPC endpoint
    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="MyResponse",
        ),
    )
```

## Proto Files

Your proto should include a `GetLastResult` method for downstream services:

```protobuf
service MyService {
  rpc ProcessData(Request) returns (Response);
  rpc GetLastResult(Empty) returns (Response);  // For downstream to fetch
}
```

## Docker

```bash
docker build -t my-service .
docker run -p 8080:8080 -p 50051:50051 my-service
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | HTTP control interface port |
| `GRPC_PORT` | 50051 | gRPC data interface port |
| `GRPC_HOST` | my-service | Hostname for gRPC endpoint references |

## When to Use

- Services that need structured protobuf message schemas
- Direct service-to-service data transfer (no serialization overhead)
- Operations completing in < 30 seconds
