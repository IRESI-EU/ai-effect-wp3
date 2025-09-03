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


class ReportGeneratorService:
    """Generates summary reports from analyzed data"""
    
    def Execute(self, request, context):
        logger.info(f"Generating report from: {request.input_file} -> {request.output_file}")
        
        try:
            # Read analyzed data
            input_path = Path(request.input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {request.input_file}")
            
            df = pd.read_csv(input_path)
            
            # Generate summary statistics
            total_records = len(df)
            anomaly_count = df['anomaly_detected'].sum()
            avg_efficiency = df['efficiency'].mean()
            max_power = df['power'].max()
            min_power = df['power'].min()
            
            # Create summary report
            report_data = {
                'metric': [
                    'Total Records',
                    'Anomalies Detected', 
                    'Average Efficiency',
                    'Max Power (W)',
                    'Min Power (W)',
                    'Anomaly Rate (%)'
                ],
                'value': [
                    total_records,
                    int(anomaly_count),
                    round(avg_efficiency, 3),
                    max_power,
                    min_power,
                    round((anomaly_count / total_records) * 100, 2)
                ]
            }
            
            # Save report
            output_path = Path(request.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report_df = pd.DataFrame(report_data)
            report_df.to_csv(output_path, index=False)
            
            message = f"Generated summary report with {len(report_data['metric'])} metrics, saved to {request.output_file}"
            logger.info(message)
            
            # TODO: Return energy_pb2.ExecuteResponse(success=True, message=message)
            return {"success": True, "message": message}  # Placeholder
            
        except Exception as e:
            error_msg = f"Failed to generate report: {str(e)}"
            logger.error(error_msg)
            # TODO: Return energy_pb2.ExecuteResponse(success=False, message=error_msg)
            return {"success": False, "message": error_msg}  # Placeholder


def serve(port: int = 50053):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # TODO: Add servicer when proto is generated
    # energy_pb2_grpc.add_ContainerExecutorServicer_to_server(
    #     ReportGeneratorService(), server
    # )
    
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"Report Generator service listening on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.stop(0)


if __name__ == "__main__":
    serve()