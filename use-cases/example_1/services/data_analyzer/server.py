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


class DataAnalyzerService:
    """Analyzes energy data and detects anomalies"""
    
    def Execute(self, request, context):
        logger.info(f"Analyzing data from: {request.input_file} -> {request.output_file}")
        
        try:
            # Read input CSV file
            input_path = Path(request.input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {request.input_file}")
            
            df = pd.read_csv(input_path)
            
            # Perform analysis
            analyzed_data = []
            for _, row in df.iterrows():
                power = float(row['power_consumption'])
                voltage = float(row['voltage'])
                current = float(row['current'])
                
                # Calculate efficiency
                efficiency = power / (voltage * current) if (voltage * current) != 0 else 0
                
                # Detect anomalies (simple threshold)
                anomaly = efficiency < 0.1 or efficiency > 0.95
                status = "anomaly" if anomaly else "normal"
                
                analyzed_data.append({
                    'timestamp': row['timestamp'],
                    'household_id': row['household_id'],
                    'power': power,
                    'efficiency': efficiency,
                    'status': status,
                    'anomaly_detected': anomaly
                })
            
            # Save analyzed data
            output_path = Path(request.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            analyzed_df = pd.DataFrame(analyzed_data)
            analyzed_df.to_csv(output_path, index=False)
            
            message = f"Analyzed {len(analyzed_data)} records, saved to {request.output_file}"
            logger.info(message)
            
            # TODO: Return energy_pb2.ExecuteResponse(success=True, message=message)
            return {"success": True, "message": message}  # Placeholder
            
        except Exception as e:
            error_msg = f"Failed to analyze data: {str(e)}"
            logger.error(error_msg)
            # TODO: Return energy_pb2.ExecuteResponse(success=False, message=error_msg)
            return {"success": False, "message": error_msg}  # Placeholder


def serve(port: int = 50052):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # TODO: Add servicer when proto is generated
    # energy_pb2_grpc.add_ContainerExecutorServicer_to_server(
    #     DataAnalyzerService(), server
    # )
    
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"Data Analyzer service listening on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.stop(0)


if __name__ == "__main__":
    serve()