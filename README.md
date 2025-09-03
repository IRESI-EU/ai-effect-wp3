# AI-Effect Orchestrator with Example Services

A complete orchestration system for AI-Effect services with tools for generating deployment configurations from service definitions.

## Project Structure

```
ai-effect-wp3/
├── orchestrator/                                    # Orchestration tools and platform exports
│   ├── scripts/                                     # Generation tools
│   │   ├── docker-compose-generator.py              # Generate docker-compose from onboarding export
│   │   └── onboarding-export-generator.py           # Generate onboarding export from services
│   └── use-cases-platform/                         # Generated AI-Effect export packages
│       └── example-1/                              # Example onboarding export
│           ├── blueprint.json                       # Pipeline topology definition
│           ├── dockerinfo.json                      # Docker image mappings
│           └── microservice/                        # Service proto files
│               ├── data_generator1.proto
│               ├── data_analyzer1.proto
│               └── report_generator1.proto
├── use-cases/                                       # Service implementations
│   └── example_1/                                  # Example energy processing pipeline
│       ├── connections.json                        # Pipeline topology configuration
│       ├── docker-compose.yml                      # Development deployment
│       ├── data/                                   # Shared data directory
│       └── services/                               # Individual services
│           ├── data_generator/                     # Energy data generation service
│           │   ├── proto/data_generator.proto      # Service-specific protocol definition
│           │   ├── server.py                       # gRPC service implementation
│           │   ├── Dockerfile                      # Container build instructions
│           │   └── requirements.txt                # Python dependencies
│           ├── data_analyzer/                      # Energy data analysis service
│           │   ├── proto/data_analyzer.proto
│           │   ├── server.py
│           │   ├── Dockerfile
│           │   └── requirements.txt
│           └── report_generator/                   # Report generation service
│               ├── proto/report_generator.proto
│               ├── server.py
│               ├── Dockerfile
│               └── requirements.txt
└── README.md                                       # This file
```

## Architecture Overview

The AI-Effect orchestrator follows a three-phase approach:

1. **Service Development Phase**: Developers create individual services with their own proto files in `use-cases/`
2. **Onboarding Export Phase**: Services are packaged into AI-Effect onboarding exports in `orchestrator/use-cases-platform/`
3. **Deployment Phase**: Onboarding exports are converted to deployment configurations

## Tools

### 1. Onboarding Export Generator

Converts a use case directory with services into an AI-Effect onboarding export package.

**Location**: `orchestrator/scripts/onboarding-export-generator.py`

**Usage**:
```bash
python orchestrator/scripts/onboarding-export-generator.py use-cases/example_1 orchestrator/use-cases-platform/example-1 --overwrite
```

**What it does**:
- Scans services directory for proto files
- Parses proto files to extract RPC methods and message types
- Reads `connections.json` to determine service topology
- Generates `blueprint.json` with proper AI-Effect format including service connections
- Generates `dockerinfo.json` with Docker image mappings
- Copies proto files to microservice directory with AI-Effect naming convention

**Requires**: `connections.json` file defining service connections:
```json
{
  "pipeline": {
    "name": "Pipeline Name",
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

### 2. Docker Compose Generator

Converts an AI-Effect onboarding export into a docker-compose.yml for deployment.

**Location**: `orchestrator/scripts/docker-compose-generator.py`

**Usage**:
```bash
python orchestrator/scripts/docker-compose-generator.py orchestrator/use-cases-platform/example-1
```

**What it does**:
- Reads `blueprint.json` for service topology and connections
- Reads `dockerinfo.json` for Docker image mappings
- Generates complete docker-compose.yml with:
  - Service definitions with auto-assigned ports starting from 50051
  - Network configuration (ai-effect-pipeline)
  - Shared volumes for data exchange
  - Service dependencies based on blueprint connections
  - Environment variables for gRPC configuration

**Output**: `docker-compose.yml` in the onboarding export directory that can be deployed anywhere

## Example Services

The project includes three example services for energy data processing:

1. **Data Generator** (port 50051): Generates synthetic energy consumption data
2. **Data Analyzer** (port 50052): Analyzes data for anomalies and calculates efficiency
3. **Report Generator** (port 50053): Creates summary reports from analyzed data

Each service:
- Has its own protobuf definition in `proto/` subdirectory
- Implements gRPC service interface
- Can be built as a Docker container
- Follows AI-Effect service patterns

## Workflows

### 1. Development Workflow

Work directly with services for development and testing:

```bash
# Start services for development
cd use-cases/example_1
docker-compose up --build

# Services available at:
# - Data Generator: localhost:50051
# - Data Analyzer: localhost:50052
# - Report Generator: localhost:50053
```

### 2. Production Deployment Workflow

Generate deployment configurations from service definitions:

```bash
# Step 1: Generate onboarding export from services
python orchestrator/scripts/onboarding-export-generator.py \
  use-cases/example_1 \
  orchestrator/use-cases-platform/my-pipeline

# Step 2: Generate docker-compose.yml from export
python orchestrator/scripts/docker-compose-generator.py \
  orchestrator/use-cases-platform/my-pipeline

# Step 3: Deploy anywhere
docker-compose -f orchestrator/use-cases-platform/my-pipeline/docker-compose.yml up -d
```

### 3. Using Existing Platform Export

Deploy pre-generated onboarding exports:

```bash
# Generate deployment config from existing export
python orchestrator/scripts/docker-compose-generator.py orchestrator/use-cases-platform/example-1

# Deploy the services
docker-compose -f orchestrator/use-cases-platform/example-1/docker-compose.yml up -d
```

## Service Connection Configuration

Define service connections in `connections.json` within your use case directory:

```json
{
  "pipeline": {
    "name": "Energy Data Processing Pipeline",
    "description": "Sequential processing of energy data through generation, analysis, and reporting",
    "start_service": "data_generator",
    "connections": [
      {
        "from_service": "data_generator",
        "from_method": "GenerateData",
        "to_service": "data_analyzer",
        "to_method": "AnalyzeData"
      },
      {
        "from_service": "data_analyzer", 
        "from_method": "AnalyzeData",
        "to_service": "report_generator",
        "to_method": "GenerateReport"
      }
    ]
  }
}
```

**Connection Format**:
- `from_service`: Name of source service directory
- `from_method`: RPC method name from source service proto
- `to_service`: Name of target service directory  
- `to_method`: RPC method name from target service proto

## Script Details

### onboarding-export-generator.py

**Arguments**:
- `use_case_dir`: Path to use case directory (e.g., `use-cases/example_1`)
- `output_dir`: Path to output directory in platform (e.g., `orchestrator/use-cases-platform/example-1`)
- `--overwrite`: Overwrite existing output directory

**Process**:
1. Scans `services/` directory for subdirectories with `proto/` folders
2. Parses each proto file to extract service names and RPC methods
3. Loads `connections.json` to understand pipeline topology
4. Creates AI-Effect compatible `blueprint.json` with proper service connections
5. Creates `dockerinfo.json` mapping containers to Docker images
6. Copies proto files to `microservice/` with AI-Effect naming (adds '1' suffix)

### docker-compose-generator.py

**Arguments**:
- `onboarding_dir`: Path to AI-Effect onboarding export directory

**Process**:
1. Reads `blueprint.json` to extract service definitions and connections
2. Reads `dockerinfo.json` to get Docker image mappings
3. Generates docker-compose.yml with:
   - Services using pre-built images from registry
   - Ports auto-assigned starting from 50051
   - AI-Effect pipeline network
   - Shared data volumes
   - Proper service dependencies

## Key Features

- **Service Isolation**: Each service has its own proto file and implementation
- **Flexible Topology**: Define any pipeline structure via connections.json
- **Container Ready**: All services built as Docker containers
- **AI-Effect Compatible**: Generates standard AI-Effect onboarding exports
- **Deployment Agnostic**: Generated docker-compose.yml works anywhere
- **Development Friendly**: Separate development and production configurations
- **Platform Integration**: Exports can be used with AI-Effect platform orchestrators

## Dependencies

```bash
pip install PyYAML  # For docker-compose generation
```

All other dependencies are handled per-service via requirements.txt files.

## Notes

- Services use insecure gRPC channels (suitable for development/internal networks)
- Ports are auto-assigned starting from 50051 in generated docker-compose.yml
- Generated exports use localhost:5000 registry (customize as needed for your registry)
- Data directory is shared between services via Docker volumes
- The `use-cases-platform/` directory mimics what would be downloaded from the AI-Effect platform