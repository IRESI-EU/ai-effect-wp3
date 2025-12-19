#!/bin/bash
set -e

echo "Building and starting protobuf-based energy pipeline services..."
docker compose up --build -d

echo ""
echo "Services started:"
echo "  - input-provider:   http://localhost:18081"
echo "  - data-generator:   http://localhost:18082"
echo "  - data-analyzer:    http://localhost:18083"
echo "  - report-generator: http://localhost:18084"
echo ""
echo "To submit a workflow, run:"
echo "  ./scripts/submit-workflow.sh"
