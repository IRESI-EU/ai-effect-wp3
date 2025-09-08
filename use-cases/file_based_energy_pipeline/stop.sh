#!/bin/bash

echo "Stopping and removing file-based energy pipeline containers..."
docker compose down --remove-orphans

echo "Pipeline containers stopped and removed."
echo ""
echo "To also remove volumes (will delete data), run:"
echo "  docker compose down -v"