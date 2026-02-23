#!/bin/bash
set -e

cd "$(dirname "$0")"

docker network create ai-effect-services 2>/dev/null || true

echo "Building and starting protobuf-based energy pipeline..."
docker compose up --build -d

echo ""
echo "Services:"
echo "  input-provider:   http://localhost:18081 (gRPC: 50051)"
echo "  data-generator:   http://localhost:18082 (gRPC: 50052)"
echo "  data-analyzer:    http://localhost:18083 (gRPC: 50053)"
echo "  report-generator: http://localhost:18084 (gRPC: 50054)"
echo ""
echo "Check logs: docker compose logs -f"
