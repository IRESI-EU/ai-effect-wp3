#!/bin/bash

echo "Stopping Protobuf-Based Energy Pipeline Services..."
echo "====================================================="

# Stop and remove containers
docker compose down

echo ""
echo "Services stopped successfully!"
echo ""
echo "To remove volumes as well, run: docker compose down -v"
echo "To start services again: ./start.sh"