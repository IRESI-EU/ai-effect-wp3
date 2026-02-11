#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USE_CASE_DIR="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$USE_CASE_DIR/export"

API_URL="${API_URL:-http://localhost:18000}"

# Read generated blueprint and dockerinfo
BLUEPRINT=$(cat "$EXPORT_DIR/blueprint.json")
DOCKERINFO=$(cat "$EXPORT_DIR/dockerinfo.json")

# Combine into workflow submission payload
PAYLOAD=$(jq -n --argjson blueprint "$BLUEPRINT" --argjson dockerinfo "$DOCKERINFO" \
  '{"blueprint": $blueprint, "dockerinfo": $dockerinfo}')

echo "Submitting Germany node workflow to orchestrator at $API_URL..."
RESPONSE=$(curl -s -X POST "$API_URL/workflows" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

WORKFLOW_ID=$(echo "$RESPONSE" | jq -r .workflow_id)

if [ "$WORKFLOW_ID" = "null" ] || [ -z "$WORKFLOW_ID" ]; then
    echo "Failed to submit workflow:"
    echo "$RESPONSE" | jq .
    exit 1
fi

echo "Workflow submitted!"
echo "Workflow ID: $WORKFLOW_ID"
echo ""
echo "Workers will automatically process this workflow."
echo ""
echo "To check status:"
echo "  curl $API_URL/workflows/$WORKFLOW_ID | jq ."
echo ""
echo "To watch worker logs:"
echo "  cd ../../orchestrator && docker compose logs -f worker"
