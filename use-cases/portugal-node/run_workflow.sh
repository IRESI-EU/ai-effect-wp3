#!/bin/bash
# TEF Services workflow demonstration

set -e

DATA_PROVISION_URL="http://localhost:8001"
KNOWLEDGE_STORE_URL="http://localhost:8002"
SYNTHETIC_DATA_URL="http://localhost:8003"

USERNAME="demo_user"
MODEL_NAME="wind_energy_model_$(date +%s)"
WORKFLOW_DIR="/tmp/tef_workflow_$(date +%s)"

echo "=========================================="
echo "TEF Services Workflow"
echo "=========================================="
echo ""
echo "Working directory: $WORKFLOW_DIR"
mkdir -p "$WORKFLOW_DIR"
cd "$WORKFLOW_DIR"
echo ""

# STEP 1: Get data
echo "=========================================="
echo "STEP 1: Loading dataset"
echo "=========================================="
echo ""

if [ -f /home/amir/code/aieffect/amir/mocks/tef-services/synthetic_data_generation/real_data.csv ]; then
    echo "Loading wind energy dataset..."
    head -1001 /home/amir/code/aieffect/amir/mocks/tef-services/synthetic_data_generation/real_data.csv | \
        sed '1s/datetime/timestamp/' > wind_energy_raw.csv
    ROWS=$(wc -l < wind_energy_raw.csv)
    echo "Loaded $ROWS rows"
    head -3 wind_energy_raw.csv
else
    echo "Dataset not found, using API example..."
    EXAMPLE_DATA=$(curl -s "$KNOWLEDGE_STORE_URL/examples/Wind%20Energy")
    echo "$EXAMPLE_DATA" | jq -r '.data | (.[0] | keys_unsorted) as $keys | $keys, map([.[$keys[]]])[] | @csv' > wind_energy_raw.csv 2>/dev/null
    ROWS=$(wc -l < wind_energy_raw.csv)
    echo "Loaded $ROWS rows (may not be sufficient for training)"
fi
echo ""

# STEP 2: Feature engineering
echo "=========================================="
echo "STEP 2: Feature engineering"
echo "=========================================="
echo ""

echo "Applying DatetimeFeatures..."
FUNCTION_NAME="DatetimeFeatures"
FUNCTION_KWARGS='{"season": "hour"}'
ENCODED_KWARGS=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$FUNCTION_KWARGS'))")

curl -s -X POST "$KNOWLEDGE_STORE_URL/functions/apply?feature_function_name=$FUNCTION_NAME&feature_function_kwargs_str=$ENCODED_KWARGS" \
  -F "file=@wind_energy_raw.csv" \
  -o wind_energy_with_features.json

if grep -q '"detail"' wind_energy_with_features.json 2>/dev/null; then
    echo "Error: Feature engineering failed"
    cat wind_energy_with_features.json | jq '.'
    exit 1
fi

if [ -f wind_energy_with_features.json ]; then
    FEATURE_ROWS=$(cat wind_energy_with_features.json | jq '. | length' 2>/dev/null)
    if [ -n "$FEATURE_ROWS" ] && [ "$FEATURE_ROWS" -gt 0 ]; then
        echo "Processed $FEATURE_ROWS rows"

        cat wind_energy_with_features.json | jq -r '(.[0] | keys_unsorted) as $keys | $keys, map([.[$keys[]]])[] | @csv' > wind_energy_featured_temp.csv

        # Convert hour to categorical to ensure discrete handling
        HOUR_COL=$(head -1 wind_energy_featured_temp.csv | tr ',' '\n' | grep -n "hour" | cut -d: -f1)

        awk -F',' -v col=$HOUR_COL 'BEGIN {OFS=","}
            NR==1 {print; next}
            {
                $col = "hour_" int($col)
                print
            }' wind_energy_featured_temp.csv > wind_energy_featured.csv

        rm wind_energy_featured_temp.csv
        echo "Hour column converted to categorical format"
    else
        echo "Error: Unexpected response format"
        exit 1
    fi
else
    echo "Error: Feature engineering failed"
    exit 1
fi
echo ""

# STEP 3: Train model
echo "=========================================="
echo "STEP 3: Training synthetic data model"
echo "=========================================="
echo ""

echo "Model: $MODEL_NAME"
echo "Training parameters: index_col=timestamp, epochs=5, batch_size=100"
echo ""

curl -s -X POST "$SYNTHETIC_DATA_URL/train?model_name=$MODEL_NAME&username=$USERNAME&index_col=timestamp&max_epochs=5&batch_size=100&overwrite=true" \
  -F "uploaded_file=@wind_energy_featured.csv;type=text/csv" \
  -o training_response.json

TRAIN_RESPONSE=$(cat training_response.json)

if echo "$TRAIN_RESPONSE" | jq '.' 2>/dev/null; then
    echo ""
else
    echo "$TRAIN_RESPONSE"
    echo ""
fi

if echo "$TRAIN_RESPONSE" | grep -qi 'error\|detail\|failed'; then
    echo "Training failed"
    SKIP_SYNTHETIC=true
else
    echo "Training started, waiting for completion..."
    sleep 5

    TRAINING_INFO=$(curl -s "$SYNTHETIC_DATA_URL/training_info?username=$USERNAME&model_name=$MODEL_NAME")
    echo "$TRAINING_INFO" | jq '.'

    echo "Waiting 30 seconds..."
    for i in {1..6}; do
        echo -n "."
        sleep 5
    done
    echo ""
    SKIP_SYNTHETIC=false
fi
echo ""

# STEP 4: Generate synthetic data
echo "=========================================="
echo "STEP 4: Generating synthetic data"
echo "=========================================="
echo ""

if [ "$SKIP_SYNTHETIC" = true ]; then
    echo "Skipped (training failed)"
else
    curl -s "$SYNTHETIC_DATA_URL/generate?model_name=$MODEL_NAME&username=$USERNAME&number_of_examples=10&output_format=csv" \
      -o synthetic_wind_data.csv

    if [ -f synthetic_wind_data.csv ]; then
        if grep -q '"detail"' synthetic_wind_data.csv 2>/dev/null; then
            echo "Generation failed"
            cat synthetic_wind_data.csv
        else
            SYNTH_ROWS=$(wc -l < synthetic_wind_data.csv)
            echo "Generated $SYNTH_ROWS rows"
            head -10 synthetic_wind_data.csv
        fi
    fi
fi
echo ""

# STEP 5: Query database
echo "=========================================="
echo "STEP 5: Database query"
echo "=========================================="
echo ""

QUERY_RESULT=$(curl -s -X POST "$DATA_PROVISION_URL/query?format=json" \
  -H "Content-Type: application/json" \
  -d '{"sql_query": "SELECT name, engine, total_rows FROM system.tables WHERE database = '"'"'system'"'"' LIMIT 5"}')

echo "$QUERY_RESULT" | jq '.'
echo ""

# Summary
echo "=========================================="
echo "Workflow complete"
echo "=========================================="
echo ""
echo "Output files in: $WORKFLOW_DIR"
ls -lh "$WORKFLOW_DIR"
echo ""
