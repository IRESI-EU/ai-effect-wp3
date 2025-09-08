#!/bin/bash

echo "Starting file-based energy pipeline..."
docker compose up --build -d

echo "Pipeline services started. You can check status with:"
echo "  docker compose ps"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"