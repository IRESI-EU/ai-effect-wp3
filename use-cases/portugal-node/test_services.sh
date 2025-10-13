#!/bin/bash
# Test script for TEF Services

set +e

echo "=========================================="
echo "TEF Services Test Script"
echo "=========================================="
echo ""

DATA_PROVISION_URL="http://localhost:8001"
KNOWLEDGE_STORE_URL="http://localhost:8002"
SYNTHETIC_DATA_URL="http://localhost:8003"

test_endpoint() {
    local name=$1
    local url=$2
    echo "Testing: $name"
    echo "URL: $url"

    RESPONSE=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo "Status: $HTTP_CODE"
        echo "Response:"
        echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
        return 0
    else
        echo "Status: $HTTP_CODE (ERROR)"
        echo "Response:"
        echo "$BODY"
        return 1
    fi
}

echo "=========================================="
echo "1. Health Checks"
echo "=========================================="
echo ""

test_endpoint "Data Provision" "$DATA_PROVISION_URL/docs"
echo ""

test_endpoint "Knowledge Store" "$KNOWLEDGE_STORE_URL/functions/tags"
echo ""

test_endpoint "Synthetic Data" "$SYNTHETIC_DATA_URL/docs"
echo ""

echo "=========================================="
echo "2. Data Provision Service"
echo "=========================================="
echo ""

echo "Testing: Execute Query"
echo "URL: $DATA_PROVISION_URL/query?format=json"
QUERY_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$DATA_PROVISION_URL/query?format=json" \
  -H "Content-Type: application/json" \
  -d '{"sql_query": "SELECT 1 as test"}')
HTTP_CODE=$(echo "$QUERY_RESPONSE" | tail -n1)
BODY=$(echo "$QUERY_RESPONSE" | sed '$d')
echo "Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "3. Knowledge Store Service"
echo "=========================================="
echo ""

echo "Testing: List Functions"
echo "URL: $KNOWLEDGE_STORE_URL/functions/list"
FUNCTIONS_RESPONSE=$(curl -s -w "\n%{http_code}" "$KNOWLEDGE_STORE_URL/functions/list")
HTTP_CODE=$(echo "$FUNCTIONS_RESPONSE" | tail -n1)
BODY=$(echo "$FUNCTIONS_RESPONSE" | sed '$d')
echo "Status: $HTTP_CODE"
FUNC_COUNT=$(echo "$BODY" | jq '. | length' 2>/dev/null)
echo "Available functions: $FUNC_COUNT"
echo ""

echo "Testing: List Recipes"
echo "URL: $KNOWLEDGE_STORE_URL/recipes/list"
RECIPES_RESPONSE=$(curl -s -w "\n%{http_code}" "$KNOWLEDGE_STORE_URL/recipes/list")
HTTP_CODE=$(echo "$RECIPES_RESPONSE" | tail -n1)
BODY=$(echo "$RECIPES_RESPONSE" | sed '$d')
echo "Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "4. Synthetic Data Service"
echo "=========================================="
echo ""

echo "Testing: List Models"
echo "URL: $SYNTHETIC_DATA_URL/models?username=test_user"
MODELS_RESPONSE=$(curl -s -w "\n%{http_code}" "$SYNTHETIC_DATA_URL/models?username=test_user")
HTTP_CODE=$(echo "$MODELS_RESPONSE" | tail -n1)
BODY=$(echo "$MODELS_RESPONSE" | sed '$d')
echo "Status: $HTTP_CODE"
echo "Response:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "Services:"
echo "  Data Provision:   $DATA_PROVISION_URL/docs"
echo "  Knowledge Store:  $KNOWLEDGE_STORE_URL/docs"
echo "  Synthetic Data:   $SYNTHETIC_DATA_URL/docs"
echo ""
