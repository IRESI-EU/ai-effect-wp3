"""Input Provider service - HTTP control + gRPC data interface.

HTTP /control/execute triggers configuration generation.
gRPC GetLastResult allows downstream services to fetch the result directly.
"""

import logging
import os
import sys
import threading
from concurrent import futures

import grpc

from handler import DataReference, ExecuteRequest, ExecuteResponse, run

# Import generated protobuf classes
import input_provider_pb2
import input_provider_pb2_grpc

logger = logging.getLogger(__name__)

# Cached last result for gRPC access
_last_result: input_provider_pb2.GetConfigurationResponse | None = None
_result_lock = threading.Lock()


class InputProviderServicer(input_provider_pb2_grpc.InputProviderServicer):
    """gRPC servicer that provides cached results to downstream services."""

    def GetConfiguration(self, request, context):
        """Generate configuration (can also be called directly via gRPC)."""
        return _generate_configuration()

    def GetLastResult(self, request, context):
        """Return cached result for downstream services."""
        with _result_lock:
            if _last_result is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("No result available yet")
                return input_provider_pb2.GetConfigurationResponse(
                    success=False,
                    message="No result available",
                )
            return _last_result


def _generate_configuration(num_records: int = 10) -> input_provider_pb2.GetConfigurationResponse:
    """Generate configuration and cache it."""
    global _last_result

    response = input_provider_pb2.GetConfigurationResponse(
        success=True,
        message=f"Configuration provided: {num_records} records",
        num_records=num_records,
    )

    with _result_lock:
        _last_result = response

    return response


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
    """HTTP handler: Generate configuration, cache it, return gRPC endpoint."""
    num_records = request.parameters.get("num_records", 10)

    logger.info(f"GetConfiguration: num_records={num_records}")

    # Generate and cache result
    result = _generate_configuration(num_records)

    if not result.success:
        return ExecuteResponse(status="failed", error=result.message)

    # Return reference to gRPC endpoint where downstream can fetch the data
    grpc_host = os.environ.get("GRPC_HOST", "input-provider")
    grpc_port = os.environ.get("GRPC_PORT", "50051")

    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="GetConfigurationResponse",
        ),
    )


if __name__ == "__main__":
    # Start gRPC server in background
    grpc_server = start_grpc_server()

    # Run HTTP control interface (blocking)
    run(sys.modules[__name__])
