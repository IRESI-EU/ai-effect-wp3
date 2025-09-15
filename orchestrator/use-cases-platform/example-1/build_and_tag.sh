#!/bin/bash
set -e

echo "Building and tagging Docker images..."

# Use case directory from metadata
USE_CASE_DIR="file_based_energy_pipeline"
USE_CASE_PATH="../../../use-cases/file_based_energy_pipeline"

if [ ! -d "$USE_CASE_PATH" ]; then
    echo "Error: Use case directory not found: $USE_CASE_PATH"
    echo "Please ensure the use case directory exists relative to this script"
    exit 1
fi

echo "Building images from: $USE_CASE_PATH"

# Build images using docker compose
cd "$USE_CASE_PATH"
docker compose build

# Tag images with :latest
docker tag file_based_energy_pipeline-data-analyzer file_based_energy_pipeline-data-analyzer:latest
docker tag file_based_energy_pipeline-report-generator file_based_energy_pipeline-report-generator:latest
docker tag file_based_energy_pipeline-data-generator file_based_energy_pipeline-data-generator:latest

echo "Successfully built and tagged all images:"
echo "  - file_based_energy_pipeline-data-analyzer:latest"
echo "  - file_based_energy_pipeline-report-generator:latest"
echo "  - file_based_energy_pipeline-data-generator:latest"
echo ""
echo "You can now run: docker compose up -d"
