# AI-Effect Orchestrator and Service Pipeline Framework

A complete framework for developing, packaging, and deploying AI-Effect microservice pipelines with automated orchestration capabilities. This system provides tools for service development, export generation, and containerized deployment compatible with AI-Effect platform specifications.

## Overview

This framework implements a complete workflow for AI-Effect service pipelines, from development through deployment. It includes an orchestrator that dynamically executes workflows based on blueprint specifications, automatically managing service dependencies and execution order.

## Project Structure

```
ai-effect-wp3/
├── scripts/                                         # Build and generation tools
│   ├── build-script-generator.py                    # Generates build scripts for use cases
│   ├── onboarding-export-generator.py               # Creates platform export packages
│   └── docker-compose-generator.py                  # Generates deployment configurations
├── orchestrator/                                    # Workflow orchestrator implementation
│   ├── Dockerfile                                   # Orchestrator container build
│   ├── orchestrator.py                              # Main entry point
│   ├── requirements.txt                             # Python dependencies
│   └── src/                                         # Source code
│       ├── main.py                                  # CLI interface
│       ├── models/                                  # Data models
│       │   ├── node.py                              # Blueprint node models
│       │   └── graph.py                             # Execution graph models
│       └── services/                                # Core services
│           ├── blueprint_service.py                 # Blueprint parsing
│           ├── dockerinfo_service.py                # Network configuration
│           ├── graph_service.py                     # Dependency resolution
│           ├── grpc_service.py                      # Dynamic gRPC client
│           ├── log_service.py                       # Logging configuration
│           └── orchestration_service.py             # Workflow execution
├── use-cases/                                       # Development workspace
│   └── file_based_energy_pipeline/                 # Example pipeline
│       ├── connections.json                         # Pipeline topology
│       ├── docker-compose.yml                       # Development deployment
│       ├── build_and_tag.sh                         # Build script (generated)
│       ├── data/                                    # Shared data volume
│       └── services/                                # Service implementations
│           ├── data_generator/                      # Data generation service
│           │   ├── proto/data_generator.proto       # Service interface
│           │   ├── server.py                        # Service implementation
│           │   ├── Dockerfile                       # Container definition
│           │   └── requirements.txt                 # Dependencies
│           ├── data_analyzer/                       # Analysis service
│           │   ├── proto/data_analyzer.proto
│           │   ├── server.py
│           │   ├── Dockerfile
│           │   └── requirements.txt
│           └── report_generator/                    # Reporting service
│               ├── proto/report_generator.proto
│               ├── server.py
│               ├── Dockerfile
│               └── requirements.txt
└── use-cases-platform/                              # Platform export packages
    └── .gitignore                                   # Excludes generated content
```

## Architecture

### Four-Phase Workflow

1. **Development Phase**: Create services with protobuf interfaces in `use-cases/`
2. **Build Phase**: Generate and execute build scripts to create Docker images
3. **Export Phase**: Package services into AI-Effect platform export format
4. **Deployment Phase**: Deploy via docker-compose with orchestrator automation

### Orchestrator

The orchestrator is a containerized service that:
- Reads blueprint.json to understand pipeline topology
- Parses dockerinfo.json for service network configuration
- Dynamically compiles protobuf definitions at runtime
- Resolves service dependencies and execution order
- Executes workflows with parallel level processing
- Handles data flow between services via gRPC
- Runs as a container within the Docker network

## Quick Start Tutorial

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PyYAML library: `pip install PyYAML`

### Step 1: Generate Build Script

```bash
python scripts/build-script-generator.py use-cases/file_based_energy_pipeline
```

This creates `use-cases/file_based_energy_pipeline/build_and_tag.sh`.

### Step 2: Build Docker Images

```bash
cd use-cases/file_based_energy_pipeline
./build_and_tag.sh
cd ../..
```

This builds all service containers and tags them appropriately.

### Step 3: Generate Platform Export

```bash
python scripts/onboarding-export-generator.py \
  use-cases/file_based_energy_pipeline \
  use-cases-platform/file_based_energy_pipeline \
  --overwrite
```

This creates the platform export package with:
- blueprint.json
- dockerinfo.json
- generation_metadata.json
- microservice/*.proto files

### Step 4: Generate Deployment Configuration

```bash
python scripts/docker-compose-generator.py \
  use-cases-platform/file_based_energy_pipeline \
  --orchestrator-path orchestrator
```

This generates docker-compose.yml with orchestrator integration.

### Step 5: Deploy and Execute

```bash
cd use-cases-platform/file_based_energy_pipeline
docker compose up --build
```

The orchestrator will:
- Read the blueprint and dockerinfo configuration
- Compile protobuf definitions
- Execute the workflow in proper dependency order
- Output results and exit

View results:
```bash
docker compose logs orchestrator
```

Clean up:
```bash
docker compose down
```

## Tools Reference

### build-script-generator.py

Generates build scripts for use cases.

**Usage**:
```bash
python scripts/build-script-generator.py <use_case_dir>
```

**Arguments**:
- `use_case_dir`: Path to use case directory containing docker-compose.yml

**Process**:
1. Reads docker-compose.yml to discover services
2. Generates bash script that builds and tags all images
3. Creates executable build_and_tag.sh in use case directory

**Example**:
```bash
python scripts/build-script-generator.py use-cases/file_based_energy_pipeline
```

### onboarding-export-generator.py

Creates AI-Effect platform export packages from service definitions.

**Usage**:
```bash
python scripts/onboarding-export-generator.py <use_case_dir> <output_dir> [--overwrite]
```

**Arguments**:
- `use_case_dir`: Source directory containing services/
- `output_dir`: Target directory for export package
- `--overwrite`: Replace existing output directory

**Process**:
1. Scans services/ for proto definitions
2. Parses proto files to extract RPC interfaces
3. Reads connections.json for pipeline topology
4. Generates blueprint.json with AI-Effect format
5. Generates dockerinfo.json with network configuration
6. Creates generation_metadata.json for tracking
7. Copies proto files to microservice/ directory

**Example**:
```bash
python scripts/onboarding-export-generator.py \
  use-cases/file_based_energy_pipeline \
  use-cases-platform/my-export \
  --overwrite
```

### docker-compose-generator.py

Generates docker-compose.yml from platform export packages.

**Usage**:
```bash
python scripts/docker-compose-generator.py <export_dir> [--base-port PORT] [--orchestrator-path PATH]
```

**Arguments**:
- `export_dir`: Path to platform export directory
- `--base-port`: Starting external port (default: 50051)
- `--orchestrator-path`: Path to orchestrator directory (enables orchestrator integration)

**Process**:
1. Reads blueprint.json for service topology
2. Reads dockerinfo.json for network configuration
3. Generates docker-compose.yml with:
   - Service definitions with proper networking
   - Auto-assigned external ports
   - Shared data volumes
   - Dependency ordering
   - Orchestrator integration (if specified)

**Example**:
```bash
python scripts/docker-compose-generator.py \
  use-cases-platform/file_based_energy_pipeline \
  --orchestrator-path orchestrator
```

## Configuration Files

### connections.json

Defines pipeline topology and service relationships.

**Format**:
```json
{
  "pipeline": {
    "name": "Pipeline Name",
    "description": "Pipeline description",
    "start_service": "first_service",
    "connections": [
      {
        "from_service": "service1",
        "from_method": "MethodName",
        "to_service": "service2",
        "to_method": "MethodName"
      }
    ]
  }
}
```

**Fields**:
- `name`: Pipeline identifier
- `description`: Pipeline description
- `start_service`: Entry point service (must match docker-compose.yml service name)
- `connections`: Array of service connections
  - `from_service`: Source service name (must match docker-compose.yml service name)
  - `from_method`: Source RPC method name
  - `to_service`: Target service name (must match docker-compose.yml service name)
  - `to_method`: Target RPC method name

**Important**: Service names in connections.json MUST match the service names defined in docker-compose.yml, NOT the directory names. For example, if docker-compose.yml defines `data-generator:` (with hyphen), connections.json must use `"from_service": "data-generator"` (with hyphen), even if the directory is named `data_generator/` (with underscore).

### blueprint.json

AI-Effect platform format for pipeline topology.

**Generated fields**:
- `nodes`: Service definitions with container names and images
- `operation_signature_list`: RPC methods and connections
- `pipeline_id`: Unique identifier
- `name`: Pipeline name
- `version`: Format version

### dockerinfo.json

Network configuration for orchestrator.

**Format**:
```json
{
  "docker_info_list": [
    {
      "container_name": "service1",
      "ip_address": "service1",
      "port": "50051"
    }
  ]
}
```

**Fields**:
- `container_name`: Docker container name
- `ip_address`: Service hostname (container name for Docker DNS)
- `port`: Internal gRPC port (50051 for all services)

## Workflows

### Development Workflow

For local service development and testing:

```bash
cd use-cases/file_based_energy_pipeline
docker compose up --build
```

Services run independently without orchestrator. Useful for:
- Service development
- Interface testing
- Debugging individual components

### Platform Export Workflow

Complete workflow from development to deployment:

```bash
# 1. Generate build script
python scripts/build-script-generator.py use-cases/file_based_energy_pipeline

# 2. Build images
cd use-cases/file_based_energy_pipeline
./build_and_tag.sh
cd ../..

# 3. Create export package
python scripts/onboarding-export-generator.py \
  use-cases/file_based_energy_pipeline \
  use-cases-platform/file_based_energy_pipeline \
  --overwrite

# 4. Generate deployment config
python scripts/docker-compose-generator.py \
  use-cases-platform/file_based_energy_pipeline \
  --orchestrator-path orchestrator

# 5. Deploy and execute
cd use-cases-platform/file_based_energy_pipeline
docker compose up --build

# 6. View results
docker compose logs orchestrator

# 7. Clean up
docker compose down
```

### Platform Download Workflow

Deploy packages downloaded from AI-Effect platform:

```bash
# Generate deployment configuration
python scripts/docker-compose-generator.py \
  path/to/downloaded/export \
  --orchestrator-path orchestrator

# Deploy
cd path/to/downloaded/export
docker compose up --build
```

## Example Pipeline

The included file_based_energy_pipeline demonstrates:

### Services

1. **data_generator**: Generates synthetic energy consumption data
   - Input: Number of records, output format
   - Output: CSV file with timestamp, energy, efficiency data

2. **data_analyzer**: Analyzes energy data for anomalies
   - Input: Data file path, anomaly threshold
   - Output: Analyzed data with anomaly flags

3. **report_generator**: Creates summary reports
   - Input: Analyzed data file, report format
   - Output: Summary statistics and report file

### Pipeline Flow

```
data_generator (GenerateData)
    |
    v
data_analyzer (AnalyzeData)
    |
    v
report_generator (GenerateReport)
```

### Execution

The orchestrator:
1. Identifies data_generator as start node (no dependencies)
2. Executes GenerateData with initial parameters
3. Passes output to data_analyzer as input
4. Executes AnalyzeData
5. Passes output to report_generator
6. Executes GenerateReport
7. Outputs final results

## Technical Details

### Port Configuration

- Internal ports: All services listen on 50051 (configured via GRPC_PORT environment variable)
- External ports: Auto-assigned starting from 50051 in docker-compose.yml
- Orchestrator uses internal ports for service communication
- Host access uses external port mapping

### Docker Networking

- Network: ai-effect-pipeline (bridge driver)
- Service discovery: Docker DNS resolves container names
- Orchestrator runs inside network for service access
- Volume mount: Export directory mounted to /export in orchestrator

### Orchestrator Operation

1. Mounts export directory as read-only volume
2. Parses blueprint.json for workflow definition
3. Reads dockerinfo.json for service addresses
4. Compiles proto files dynamically using grpc_tools.protoc
5. Builds execution graph with dependency resolution
6. Determines execution order by levels
7. Executes nodes level-by-level with parallel processing within levels
8. Passes outputs as inputs to dependent nodes
9. Outputs results and exits

### Data Flow

Services communicate via:
- gRPC for method invocation and response
- Shared volume for file-based data exchange
- JSON-serializable message types

## Dependencies

### Framework Tools

```bash
pip install PyYAML
```

### Orchestrator

```bash
pip install grpcio grpcio-tools protobuf
```

### Services

Each service has requirements.txt specifying:
- grpcio
- grpcio-tools
- protobuf
- Service-specific dependencies (pandas, numpy, etc.)

## Platform Compatibility

### AI-Effect Platform Format

Generated exports conform to AI-Effect platform specifications:
- Blueprint format version 2.0
- Standard dockerinfo structure
- Protobuf definitions in microservice/ directory
- Container naming with numeric suffixes

### Deployment Portability

Generated docker-compose.yml files:
- Use relative paths for portability
- Work on any host with Docker
- Support both local and remote images
- Include orchestrator for automated execution

## Notes

- Services use insecure gRPC channels (suitable for internal networks)
- All services standardized on internal port 50051
- External port mapping prevents conflicts
- Export packages contain no source code (platform simulation)
- Images must be built before export generation
- Orchestrator compiles proto files at runtime
- Shared data volume enables file-based communication
- Container names used for Docker DNS resolution

## License

This framework is developed for AI-Effect consortium partners and follows project licensing agreements.
