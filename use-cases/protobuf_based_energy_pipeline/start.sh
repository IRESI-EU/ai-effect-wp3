#!/bin/bash

echo "Starting Protobuf-Based Energy Pipeline Services..."
echo "====================================================="

# Build and start all services in detached mode
docker compose up --build -d

echo ""
echo "Services started successfully!"
echo ""
echo "HTTP Control Interface (for orchestrator):"
echo "  - Input Provider:    http://localhost:18081/control/execute"
echo "  - Data Generator:    http://localhost:18082/control/execute"
echo "  - Data Analyzer:     http://localhost:18083/control/execute"
echo "  - Report Generator:  http://localhost:18084/control/execute"
echo ""
echo "gRPC Data Interface (for direct service-to-service communication):"
echo "  - Input Provider:    localhost:50051"
echo "  - Data Generator:    localhost:50052"
echo "  - Data Analyzer:     localhost:50053"
echo "  - Report Generator:  localhost:50054"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: ./stop.sh"
echo "To submit workflow: ./scripts/submit-workflow.sh"
