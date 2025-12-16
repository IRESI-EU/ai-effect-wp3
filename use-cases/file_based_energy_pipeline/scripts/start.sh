#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p data
docker compose up --build -d
echo "Pipeline services running:"
echo "  - input-provider:   http://localhost:18081"
echo "  - data-generator:   http://localhost:18082"
echo "  - data-analyzer:    http://localhost:18083"
echo "  - report-generator: http://localhost:18084"
