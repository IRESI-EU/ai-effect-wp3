"""Data Generator service - HTTP control + gRPC data interface.

HTTP /control/execute triggers data generation.
Calls input_provider via gRPC to get configuration.
gRPC GetLastResult allows downstream services to fetch the result directly.
"""

import logging
import os
import random
import sys
import threading
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

# Cached last result for gRPC access
_last_result: data_generator_pb2.GenerateDataResponse | None = None
_result_lock = threading.Lock()


class DataGeneratorServicer(data_generator_pb2_grpc.DataGeneratorServiceServicer):
    """gRPC servicer that provides cached results to downstream services."""

    def GenerateData(self, request, context):
        """Generate data (can also be called directly via gRPC)."""
        return _generate_data(request.num_records)

    def GetLastResult(self, request, context):
        """Return cached result for downstream services."""
        with _result_lock:
            if _last_result is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No result available yet")
                return data_generator_pb2.GenerateDataResponse(
                    success=False,
                    message="No result available",
                )
            return _last_result


def _generate_data(num_records: int) -> data_generator_pb2.GenerateDataResponse:
    """Generate synthetic energy data and cache it."""
    global _last_result

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

    with _result_lock:
        _last_result = response

    logger.info(response.message)
    return response


def _fetch_config_from_upstream(grpc_uri: str) -> input_provider_pb2.GetConfigurationResponse:
    """Fetch configuration from input_provider via gRPC."""
    logger.info(f"Fetching config from {grpc_uri}")

    channel = grpc.insecure_channel(grpc_uri)
    stub = input_provider_pb2_grpc.InputProviderStub(channel)

    try:
        response = stub.GetLastResult(input_provider_pb2.Empty())
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

    # Get upstream gRPC endpoint from inputs
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

    logger.info(f"GenerateData: num_records={num_records}")

    # Generate and cache result
    result = _generate_data(num_records)

    if not result.success:
        return ExecuteResponse(status="failed", error=result.message)

    # Return reference to gRPC endpoint where downstream can fetch the data
    grpc_host = os.environ.get("GRPC_HOST", "data-generator")
    grpc_port = os.environ.get("GRPC_PORT", "50051")

    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="GenerateDataResponse",
        ),
    )


if __name__ == "__main__":
    # Start gRPC server in background
    grpc_server = start_grpc_server()

    # Run HTTP control interface (blocking)
    run(sys.modules[__name__])
