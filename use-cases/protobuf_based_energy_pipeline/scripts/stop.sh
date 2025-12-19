#!/bin/bash
set -e

echo "Stopping protobuf-based energy pipeline services..."
docker compose down

echo "Services stopped."
