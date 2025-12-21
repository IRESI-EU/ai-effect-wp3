"""Data Generator service - HTTP control + gRPC data interface.

HTTP /control/execute triggers data generation.
Calls input_provider.GetConfiguration directly via gRPC.
Downstream services call GenerateData directly via gRPC.
"""

import logging
import os
import random
import sys
from concurrent import futures
from datetime import datetime, timedelta

import grpc

from handler import DataReference, ExecuteRequest, ExecuteResponse, run

# Import generated protobuf classes
import common_pb2
import data_generator_pb2
import data_generator_pb2_grpc
import input_provider_pb2
import input_provider_pb2_grpc

logger = logging.getLogger(__name__)

# Store current num_records for gRPC calls
_current_num_records = 10


class DataGeneratorServicer(data_generator_pb2_grpc.DataGeneratorServiceServicer):
    """gRPC servicer for data generation requests."""

    def GenerateData(self, request, context):
        """Generate data. Called directly by downstream services."""
        num_records = request.num_records if request.num_records > 0 else _current_num_records
        return _generate_data(num_records)


def _generate_data(num_records: int, verbose: bool = False) -> data_generator_pb2.GenerateDataResponse:
    """Generate synthetic energy data."""
    logger.info(f"Generating {num_records} records")

    response = data_generator_pb2.GenerateDataResponse()
    base_time = datetime.now()
    households = ["HH-001", "HH-002", "HH-003", "HH-004", "HH-005"]

    for i in range(num_records):
        record = common_pb2.EnergyRecord()
        timestamp = base_time + timedelta(minutes=i)
        record.timestamp = timestamp.isoformat() + "Z"
        record.household_id = households[i % len(households)]

        base_consumption = 120.0 + (i % 10) * 5
        record.power_consumption = base_consumption + random.uniform(-10, 10)
        record.voltage = 230.0 + random.uniform(-5, 5)
        record.current = record.power_consumption / record.voltage

        response.records.append(record)

    response.success = True
    response.message = f"Successfully generated {len(response.records)} energy records"

    if verbose:
        logger.info("=" * 60)
        logger.info("DATA GENERATOR - Generated Records")
        logger.info("=" * 60)
        logger.info(f"  Total records: {len(response.records)}")
        logger.info(f"  Households: {', '.join(households)}")
        logger.info("  Sample records:")
        for i, rec in enumerate(response.records[:3]):
            logger.info(f"    [{i+1}] {rec.household_id}: {rec.power_consumption:.1f}W @ {rec.voltage:.1f}V")
        if len(response.records) > 3:
            logger.info(f"    ... and {len(response.records) - 3} more")
        logger.info("=" * 60)
    else:
        logger.info(response.message)
    return response


def _fetch_config_from_upstream(grpc_uri: str) -> input_provider_pb2.GetConfigurationResponse:
    """Fetch configuration from input_provider via gRPC."""
    logger.info(f"Calling GetConfiguration on {grpc_uri}")

    channel = grpc.insecure_channel(grpc_uri)
    stub = input_provider_pb2_grpc.InputProviderStub(channel)

    try:
        # Call the actual method directly
        response = stub.GetConfiguration(input_provider_pb2.GetConfigurationRequest())
        logger.info(f"Got config: num_records={response.num_records}")
        return response
    finally:
        channel.close()


def start_grpc_server():
    """Start gRPC server in background thread."""
    grpc_port = os.environ.get("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    data_generator_pb2_grpc.add_DataGeneratorServiceServicer_to_server(
        DataGeneratorServicer(), server
    )
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    logger.info(f"gRPC server started on port {grpc_port}")
    return server


# --- HTTP Control Interface ---

def execute_GenerateData(request: ExecuteRequest) -> ExecuteResponse:
    """HTTP handler: Fetch config via gRPC, generate data, return gRPC endpoint."""
    global _current_num_records

    num_records = 10  # default

    for inp in request.inputs:
        if inp.get("protocol") == "grpc":
            # Fetch config from input_provider via gRPC
            upstream_uri = inp.get("uri")
            try:
                config = _fetch_config_from_upstream(upstream_uri)
                num_records = config.num_records
            except grpc.RpcError as e:
                logger.error(f"Failed to fetch config: {e}")
                return ExecuteResponse(status="failed", error=f"Failed to fetch config: {e}")

    # Override with parameters if provided
    num_records = request.parameters.get("num_records", num_records)
    _current_num_records = num_records

    logger.info(f"GenerateData: num_records={num_records}")

    # Generate data with verbose output
    result = _generate_data(num_records, verbose=True)

    if not result.success:
        return ExecuteResponse(status="failed", error=result.message)

    # Return reference to gRPC endpoint where downstream can call GenerateData
    grpc_host = os.environ.get("GRPC_HOST", "data-generator")
    grpc_port = os.environ.get("GRPC_PORT", "50051")

    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="GenerateData",  # Method name to call
        ),
    )


if __name__ == "__main__":
    # Start gRPC server in background
    grpc_server = start_grpc_server()

    # Run HTTP control interface (blocking)
    run(sys.modules[__name__])
