"""Service implementation - HTTP control + gRPC data exchange.

This template shows how to:
1. Expose HTTP control interface for orchestrator
2. Run gRPC server for data exchange with other services
3. Call upstream services via gRPC to fetch input data
4. Cache results for downstream services to fetch via gRPC

Each method should be named execute_<MethodName> where MethodName
matches the operation name in the blueprint.
"""

import logging
import os
import sys
import threading
from concurrent import futures

import grpc

from handler import DataReference, ExecuteRequest, ExecuteResponse, run

# Import your generated protobuf classes
# import my_service_pb2
# import my_service_pb2_grpc
# import upstream_service_pb2
# import upstream_service_pb2_grpc

logger = logging.getLogger(__name__)

# Cached last result for gRPC access by downstream services
# _last_result: my_service_pb2.MyResponse | None = None
_last_result = None
_result_lock = threading.Lock()


# --- gRPC Server (for downstream services to fetch data) ---

# class MyServiceServicer(my_service_pb2_grpc.MyServiceServicer):
#     """gRPC servicer that provides cached results to downstream services."""
#
#     def ProcessData(self, request, context):
#         """Process data (can also be called directly via gRPC)."""
#         return _process_data(request)
#
#     def GetLastResult(self, request, context):
#         """Return cached result for downstream services."""
#         with _result_lock:
#             if _last_result is None:
#                 context.set_code(grpc.StatusCode.NOT_FOUND)
#                 context.set_details("No result available yet")
#                 return my_service_pb2.MyResponse(success=False)
#             return _last_result


def start_grpc_server():
    """Start gRPC server in background for data exchange."""
    grpc_port = os.environ.get("GRPC_PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register your servicer:
    # my_service_pb2_grpc.add_MyServiceServicer_to_server(
    #     MyServiceServicer(), server
    # )

    server.add_insecure_port(f"[::]:{grpc_port}")
    server.start()
    logger.info(f"gRPC server started on port {grpc_port}")
    return server


# --- gRPC Client (to fetch data from upstream services) ---

def fetch_from_upstream(grpc_uri: str):
    """Fetch data from upstream service via gRPC.

    Args:
        grpc_uri: The gRPC endpoint (e.g., "upstream-service:50051")

    Returns:
        The protobuf response from upstream service.
    """
    logger.info(f"Fetching data from {grpc_uri}")

    channel = grpc.insecure_channel(grpc_uri)
    # stub = upstream_service_pb2_grpc.UpstreamServiceStub(channel)

    try:
        # response = stub.GetLastResult(upstream_service_pb2.Empty())
        # return response
        pass
    finally:
        channel.close()


# --- HTTP Control Interface (for orchestrator) ---

def execute_ProcessData(request: ExecuteRequest) -> ExecuteResponse:
    """HTTP handler: Fetch data via gRPC, process it, return gRPC endpoint.

    The orchestrator calls this via HTTP. This method:
    1. Fetches input data from upstream service via gRPC
    2. Processes the data
    3. Caches the result for downstream services
    4. Returns a gRPC endpoint reference for the orchestrator to pass downstream
    """
    global _last_result

    # 1. Fetch input from upstream via gRPC (if inputs provided)
    for inp in request.inputs:
        if inp.get("protocol") == "grpc":
            upstream_uri = inp.get("uri")
            try:
                upstream_data = fetch_from_upstream(upstream_uri)
                # Use upstream_data for processing...
            except grpc.RpcError as e:
                logger.error(f"Failed to fetch from upstream: {e}")
                return ExecuteResponse(status="failed", error=str(e))

    # 2. Process the data
    # result = process(upstream_data)

    # 3. Cache result for downstream gRPC access
    # with _result_lock:
    #     _last_result = result

    # 4. Return gRPC endpoint reference
    grpc_host = os.environ.get("GRPC_HOST", "my-service")
    grpc_port = os.environ.get("GRPC_PORT", "50051")

    return ExecuteResponse(
        status="complete",
        output=DataReference(
            protocol="grpc",
            uri=f"{grpc_host}:{grpc_port}",
            format="MyResponse",  # The protobuf message type
        ),
    )


if __name__ == "__main__":
    # Start gRPC server in background (for data exchange)
    grpc_server = start_grpc_server()

    # Run HTTP control interface (blocking, for orchestrator)
    run(sys.modules[__name__])
