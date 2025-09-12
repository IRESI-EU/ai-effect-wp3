"""Main orchestration service for workflow execution."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.node import Blueprint, Node
from models.graph import ExecutionGraph, GraphNode
from services.blueprint_service import BlueprintService
from services.graph_service import GraphService
from services.grpc_service import GrpcService
from services.dockerinfo_service import DockerinfoService


class OrchestrationService:
    """Service for orchestrating workflow execution."""
    
    def __init__(self, use_case_dir: str):
        """Initialize orchestration service.
        
        Args:
            use_case_dir: Directory containing proto files, dockerinfo.json and other resources
        """
        if not use_case_dir:
            raise ValueError("use_case_dir is required")
        
        self.use_case_dir = use_case_dir
        
        self.logger = logging.getLogger(__name__)
        self.blueprint_service = BlueprintService()
        self.graph_service = GraphService()
        self.grpc_service = GrpcService()
        self.dockerinfo_service = DockerinfoService()
        
        self._execution_results = {}  # node_key -> execution result
    
    def execute_workflow(self, blueprint_path: str, 
                        initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute complete workflow from blueprint.
        
        Args:
            blueprint_path: Path to blueprint.json file
            initial_data: Initial data for start nodes
            
        Returns:
            Dict containing execution results
        """
        if not blueprint_path:
            raise ValueError("blueprint_path is required")
        
        self.logger.info(f"Starting workflow execution from: {blueprint_path}")
        
        try:
            # Load and parse blueprint
            blueprint = self.blueprint_service.load_blueprint(blueprint_path)
            
            # Build execution graph
            graph = self.graph_service.build_graph(blueprint)
            
            # Load network configuration from dockerinfo.json
            node_addresses = self.dockerinfo_service.load_dockerinfo(self.use_case_dir, blueprint.nodes)
            
            # Configure node addresses
            self._configure_node_addresses(graph, node_addresses)
            
            # Execute workflow
            results = self._execute_graph(graph, initial_data or {})
            
            self.logger.info("Workflow execution completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            raise
    
    def _configure_node_addresses(self, graph: ExecutionGraph, node_addresses: Dict[str, Dict[str, Any]]):
        """Configure node addresses from dockerinfo configuration."""
        for node in graph.all_nodes.values():
            container_name = node.node.container_name
            
            if container_name in node_addresses:
                address_info = node_addresses[container_name]
                node.node.address = address_info.get('address')
                node.node.port = address_info.get('port')
                
                self.logger.debug(f"Configured {container_name}: "
                                f"{node.node.address}:{node.node.port}")
            else:
                raise ValueError(f"No network configuration found for container: {container_name}")
    
    def _execute_graph(self, graph: ExecutionGraph, 
                      initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow graph."""
        self.logger.info("Beginning graph execution")
        
        # Get execution order
        execution_levels = self.graph_service.get_execution_order(graph)
        
        # Execute level by level
        for level_idx, level_nodes in enumerate(execution_levels):
            self.logger.info(f"Executing level {level_idx} with {len(level_nodes)} nodes")
            
            # Execute nodes in parallel within each level
            self._execute_level(level_nodes, initial_data if level_idx == 0 else {})
        
        return self._execution_results
    
    def _execute_level(self, nodes: List[GraphNode], level_initial_data: Dict[str, Any]):
        """Execute all nodes in a level (potentially in parallel)."""
        if len(nodes) == 1:
            # Single node execution
            self._execute_node(nodes[0], level_initial_data)
        else:
            # Parallel execution
            with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
                futures = []
                
                for node in nodes:
                    future = executor.submit(self._execute_node, node, level_initial_data)
                    futures.append(future)
                
                # Wait for all to complete
                for future in as_completed(futures):
                    try:
                        future.result()  # This will raise exception if node execution failed
                    except Exception as e:
                        self.logger.error(f"Node execution failed: {e}")
                        raise
    
    def _execute_node(self, graph_node: GraphNode, initial_data: Dict[str, Any]):
        """Execute a single graph node."""
        node = graph_node.node
        operation = graph_node.operation.operation_signature
        
        self.logger.info(f"Executing node: {graph_node.key}")
        
        try:
            # Compile proto files
            pb2_module, pb2_grpc_module = self.grpc_service.compile_proto(
                node.proto_uri, self.use_case_dir
            )
            
            # Create gRPC stub
            stub, channel = self.grpc_service.create_grpc_stub(
                node, operation, pb2_grpc_module
            )
            
            # Prepare request data
            request_data = self._prepare_request_data(graph_node, initial_data)
            
            # Execute gRPC call
            response = self.grpc_service.call_grpc_method(
                stub, operation, pb2_module, request_data
            )
            
            # Store result
            result = self._process_response(response)
            self._execution_results[graph_node.key] = result
            
            # Mark node as executed
            graph_node.executed = True
            
            self.logger.info(f"Node execution successful: {graph_node.key}")
            
            # Close channel
            channel.close()
            
        except Exception as e:
            self.logger.error(f"Failed to execute node {graph_node.key}: {e}")
            raise RuntimeError(f"Node execution failed: {e}")
    
    def _prepare_request_data(self, graph_node: GraphNode, 
                            initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for node execution."""
        operation_name = graph_node.operation.operation_signature.operation_name.lower()
        
        # Use initial data for start nodes, or prepare based on operation type
        if initial_data and not graph_node.dependencies:
            return initial_data
        
        # Default request data based on operation type
        # Check more specific patterns first
        if 'generatereport' in operation_name:
            return {
                'analyzed_data_path': 'data/analyzed_energy.csv',
                'report_format': 'csv'
            }
        elif 'generatedata' in operation_name:
            return {
                'num_records': 10,
                'output_format': 'csv'
            }
        elif 'analyze' in operation_name:
            return {
                'input_file_path': 'data/raw_energy.csv',
                'anomaly_threshold': 0.1
            }
        else:
            return {}
    
    def _process_response(self, response: Any) -> Dict[str, Any]:
        """Process gRPC response into dictionary."""
        result = {}
        
        # Extract fields from response
        for field in response.DESCRIPTOR.fields:
            field_name = field.name
            field_value = getattr(response, field_name)
            result[field_name] = field_value
        
        return result