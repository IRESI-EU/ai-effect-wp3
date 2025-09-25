#!/bin/bash

echo "Starting Protobuf-Based Energy Pipeline Services..."
echo "====================================================="

# Build and start all services in detached mode
docker compose up --build -d

echo ""
echo "Services started successfully!"
echo ""
echo "Services are running on:"
echo "  - Data Generator:    http://localhost:50051"
echo "  - Data Analyzer:     http://localhost:50052"
echo "  - Report Generator:  http://localhost:50053"
echo ""
echo "To view logs: docker compose logs -f"
echo "To stop services: ./stop.sh"