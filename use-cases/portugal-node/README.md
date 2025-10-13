# TEF Services Integration Testing

Integration testing for TEF services as part of WP3 orchestrator development.

These files should be copied to the root of the tef-services folder shared by the Portuguese node with WP3. If you want to run the tests, you can request the tef-services folder from the Portuguese node.

## Running the services

Copy these files to the root of the tef-services directory and run:

```bash
docker-compose -f docker-compose-all.yml up -d
sleep 30
./test_services.sh
./run_workflow.sh
```

## What the workflow does

Loads wind energy data, applies DatetimeFeatures to extract hour of day, trains DoppelGANger model, generates synthetic data, and queries the database.

## Issues encountered

**Hour feature handling**

The DatetimeFeatures function returns hour as integers 0-23. The DoppelGANger model detected these as numeric and treated them as continuous variables, so it was generating invalid values like 9.34 or 11.87 instead of proper hours.

I fixed this by converting hour values to categorical strings (hour_0, hour_1, etc.) before training. This forces the model to treat them as discrete categories. Not sure if this is what was originally intended or if there's a better approach.

The conversion happens in run_workflow.sh:

```bash
HOUR_COL=$(head -1 data.csv | tr ',' '\n' | grep -n "hour" | cut -d: -f1)
awk -F',' -v col=$HOUR_COL 'BEGIN {OFS=","}
    NR==1 {print; next}
    {$col = "hour_" int($col); print}
' input.csv > output.csv
```

**Column naming**

Knowledge Store requires "timestamp" column while Synthetic Data defaults to "datetime". The Synthetic Data service has an index_col parameter that lets you specify which column to use, so no renaming needed:

```bash
curl -X POST "http://localhost:8003/train?index_col=timestamp..." \
  -F "uploaded_file=@data.csv"
```

## Integration considerations

Some things to consider for orchestrator integration:

Services use REST APIs instead of ProtoBuf/gRPC. Will need to decide on adapter approach.

Training is asynchronous and can take time. Need to handle status polling or callbacks.

Different services may have different data format expectations that need to be handled in the orchestration layer.

## Services

Once running:
- Data Provision: http://localhost:8001/docs
- Knowledge Store: http://localhost:8002/docs
- Synthetic Data: http://localhost:8003/docs
