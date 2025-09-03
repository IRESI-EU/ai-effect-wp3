import os
import logging
import grpc
import pandas as pd
from concurrent import futures
from pathlib import Path

# TODO: Generated proto files will be imported here
# from generated import energy_pb2, energy_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataGeneratorService:
    """Generates synthetic energy data and saves to CSV"""
    
    def Execute(self, request, context):
        logger.info(f"Generating data to: {request.output_file}")
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(request.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate synthetic energy data
            data = {
                'timestamp': [f"2025-01-01T00:00:{i:02d}Z" for i in range(10)],
                'household_id': [f"HH-{i%3}" for i in range(10)],
                'power_consumption': [120.5 + i for i in range(10)],
                'voltage': [230.0] * 10,
                'current': [5.1 + (i*0.1) for i in range(10)]
            }
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            message = f"Generated {len(data['timestamp'])} records to {request.output_file}"
            logger.info(message)
            
            # TODO: Return energy_pb2.ExecuteResponse(success=True, message=message)
            return {"success": True, "message": message}  # Placeholder
            
        except Exception as e:
            error_msg = f"Failed to generate data: {str(e)}"
            logger.error(error_msg)
            # TODO: Return energy_pb2.ExecuteResponse(success=False, message=error_msg)  
            return {"success": False, "message": error_msg}  # Placeholder


def serve(port: int = 50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # TODO: Add servicer when proto is generated
    # energy_pb2_grpc.add_ContainerExecutorServicer_to_server(
    #     DataGeneratorService(), server
    # )
    
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"Data Generator service listening on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.stop(0)


if __name__ == "__main__":
    serve()