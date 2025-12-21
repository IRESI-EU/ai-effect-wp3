"""Input Provider service - HTTP control + gRPC data interface.

HTTP /control/execute triggers configuration generation.
Downstream services call GetConfiguration directly via gRPC.
"""

import logging
import os
import sys
from concurrent import futures

import grpc

from handler import DataReference, ExecuteRequest, ExecuteResponse, run

# Import generated protobuf classes
import input_provider_pb2
import input_provider_pb2_grpc

logger = logging.getLogger(__name__)

# Store current configuration for gRPC calls
_current_num_records = 10


class InputProviderServicer(input_provider_pb2_grpc.InputProviderServicer):
    """gRPC servicer for configuration requests."""

    def GetConfiguration(self, request, context):
        """Return configuration. Called directly by downstream services."""
        num_records = request.num_records if request.num_records > 0 else _current_num_records
        return input_provider_pb2.GetConfigurationResponse(
            success=True,
            message=f"Configuration provided: {num_records} records",
            num_records=num_records,
        )


def start_grpc_server():
    """Start gRPC server in background thread."""
    grpc_port = os.environ.get("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    input_provider_pb2_grpc.add_InputProviderServicer_to_server(
        InputProviderServicer(), server
    )
    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    logger.info(f"gRPC server started on port {grpc_port}")
    return server


# --- HTTP Control Interface ---

def execute_GetConfiguration(request: ExecuteRequest) -> ExecuteResponse:
    """HTTP handler: Set configuration, return gRPC endpoint for downstream."""
    global _current_num_records

    _current_num_records = request.parameters.get("num_records", 10)

    logger.info("=" * 60)
    logger.info("INPUT PROVIDER - Configuration")
    logger.info("=" * 60)
    logger.info(f"  Number of records to generate: {_current_num_records}")
    logger.info("=" * 60)

    # Return reference to gRPC endpoint where downstream can call GetConfiguration
    grpc_host = os.environ.get("GRPC_HOST", "input-provider")
    grpc_port = os.environ.get("GRPC_PORT", "50051")

    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="GetConfiguration",  # Method name to call
        ),
    )


if __name__ == "__main__":
    # Start gRPC server in background
    grpc_server = start_grpc_server()

    # Run HTTP control interface (blocking)
    run(sys.modules[__name__])
