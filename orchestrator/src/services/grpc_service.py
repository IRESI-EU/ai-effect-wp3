"""Service for dynamic gRPC proto loading and execution."""

import grpc
import logging
import importlib.util
import sys
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import subprocess

from models.node import Node, OperationSignature


class GrpcService:
    """Service for handling dynamic gRPC operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._compiled_modules = {}  # proto_path -> (pb2_module, pb2_grpc_module)
        self._temp_dirs = []  # Keep track of temp directories for cleanup
    
    def __del__(self):
        """Cleanup temporary directories."""
        for temp_dir in self._temp_dirs:
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    def compile_proto(self, proto_path: str, use_case_dir: str) -> Tuple[Any, Any]:
        """Compile proto file and return pb2 and pb2_grpc modules."""
        if not proto_path:
            raise ValueError("proto_path is required")
        
        if not use_case_dir:
            raise ValueError("use_case_dir is required")
        
        # Check if already compiled
        if proto_path in self._compiled_modules:
            self.logger.debug(f"Using cached compiled proto: {proto_path}")
            return self._compiled_modules[proto_path]
        
        full_proto_path = Path(use_case_dir) / proto_path
        if not full_proto_path.exists():
            raise FileNotFoundError(f"Proto file not found: {full_proto_path}")
        
        self.logger.info(f"Compiling proto file: {full_proto_path}")
        
        # Create temporary directory for compiled modules
        temp_dir = tempfile.mkdtemp(prefix="orchestrator_proto_")
        self._temp_dirs.append(temp_dir)
        
        try:
            # Compile proto file
            self._compile_proto_file(str(full_proto_path), temp_dir)
            
            # Load compiled modules
            pb2_module, pb2_grpc_module = self._load_compiled_modules(
                full_proto_path.name, temp_dir
            )
            
            # Cache the modules
            self._compiled_modules[proto_path] = (pb2_module, pb2_grpc_module)
            
            return pb2_module, pb2_grpc_module
            
        except Exception as e:
            self.logger.error(f"Failed to compile proto {proto_path}: {e}")
            raise RuntimeError(f"Proto compilation failed: {e}")
    
    def _compile_proto_file(self, proto_path: str, output_dir: str):
        """Compile proto file using grpc_tools.protoc."""
        try:
            from grpc_tools import protoc
            
            # Get proto directory and filename
            proto_file = Path(proto_path)
            proto_dir = str(proto_file.parent)
            proto_name = proto_file.name
            
            # Compile proto file
            protoc_args = [
                'grpc_tools.protoc',
                f'--python_out={output_dir}',
                f'--grpc_python_out={output_dir}',
                f'-I{proto_dir}',
                proto_path
            ]
            
            self.logger.debug(f"Running protoc with args: {' '.join(protoc_args[1:])}")
            
            result = protoc.main(protoc_args)
            if result != 0:
                raise RuntimeError(f"protoc failed with exit code: {result}")
            
            self.logger.debug(f"Proto compilation successful: {proto_name}")
            
        except ImportError:
            raise RuntimeError("grpc_tools not available - install with: pip install grpcio-tools")
        except Exception as e:
            raise RuntimeError(f"Proto compilation failed: {e}")
    
    def _load_compiled_modules(self, proto_filename: str, output_dir: str) -> Tuple[Any, Any]:
        """Load compiled pb2 and pb2_grpc modules."""
        proto_name = proto_filename.replace('.proto', '')
        
        pb2_filename = f"{proto_name}_pb2.py"
        pb2_grpc_filename = f"{proto_name}_pb2_grpc.py"
        
        pb2_path = Path(output_dir) / pb2_filename
        pb2_grpc_path = Path(output_dir) / pb2_grpc_filename
        
        if not pb2_path.exists():
            raise FileNotFoundError(f"Compiled pb2 file not found: {pb2_path}")
        
        if not pb2_grpc_path.exists():
            raise FileNotFoundError(f"Compiled pb2_grpc file not found: {pb2_grpc_path}")
        
        # Load pb2 module
        pb2_spec = importlib.util.spec_from_file_location(
            f"{proto_name}_pb2", str(pb2_path)
        )
        pb2_module = importlib.util.module_from_spec(pb2_spec)
        sys.modules[f"{proto_name}_pb2"] = pb2_module
        pb2_spec.loader.exec_module(pb2_module)
        
        # Load pb2_grpc module
        pb2_grpc_spec = importlib.util.spec_from_file_location(
            f"{proto_name}_pb2_grpc", str(pb2_grpc_path)
        )
        pb2_grpc_module = importlib.util.module_from_spec(pb2_grpc_spec)
        sys.modules[f"{proto_name}_pb2_grpc"] = pb2_grpc_module
        pb2_grpc_spec.loader.exec_module(pb2_grpc_module)
        
        self.logger.debug(f"Loaded compiled modules for {proto_name}")
        
        return pb2_module, pb2_grpc_module
    
    def create_grpc_stub(self, node: Node, operation: OperationSignature, 
                        pb2_grpc_module: Any) -> Any:
        """Create gRPC stub for the given node and operation."""
        if not node.address:
            raise ValueError(f"Node address not set for {node.container_name}")
        
        if not node.port:
            raise ValueError(f"Node port not set for {node.container_name}")
        
        # Build service name from operation (assume service name pattern)
        service_name = self._infer_service_name(operation.operation_name, pb2_grpc_module)
        
        self.logger.debug(f"Inferred service name: {service_name} for operation: {operation.operation_name}")
        self.logger.debug(f"Available attributes in module: {[attr for attr in dir(pb2_grpc_module) if not attr.startswith('_')]}")
        
        if not hasattr(pb2_grpc_module, service_name):
            raise AttributeError(f"Service {service_name} not found in proto module")
        
        service_stub_class = getattr(pb2_grpc_module, service_name)
        
        # Create channel and stub
        address = f"{node.address}:{node.port}"
        self.logger.debug(f"Creating gRPC stub for {service_name} at {address}")
        
        channel = grpc.insecure_channel(address)
        stub = service_stub_class(channel)
        
        return stub, channel
    
    def _infer_service_name(self, operation_name: str, pb2_grpc_module: Any) -> str:
        """Find service stub that contains the specified operation."""
        # Look for service stub classes in the module
        for attr_name in dir(pb2_grpc_module):
            if attr_name.endswith('Stub') and 'Service' in attr_name:
                # Check if this service has the operation method
                service_class = getattr(pb2_grpc_module, attr_name)
                
                # Create temporary stub to check methods
                try:
                    temp_channel = grpc.insecure_channel('localhost:0')
                    temp_stub = service_class(temp_channel)
                    
                    if hasattr(temp_stub, operation_name):
                        temp_channel.close()
                        return attr_name
                    
                    temp_channel.close()
                except:
                    continue
        
        # If no service stub contains the operation, this is an error
        available_stubs = [attr for attr in dir(pb2_grpc_module) if attr.endswith('Stub')]
        raise RuntimeError(f"No service stub found containing operation '{operation_name}'. Available stubs: {available_stubs}")
    
    def call_grpc_method(self, stub: Any, operation: OperationSignature, 
                        pb2_module: Any, request_data: Dict[str, Any]) -> Any:
        """Call gRPC method with dynamic request creation."""
        if not hasattr(stub, operation.operation_name):
            raise AttributeError(f"Operation {operation.operation_name} not found in stub")
        
        # Create request message
        request_class = getattr(pb2_module, operation.input_message_name)
        request = request_class()
        
        # Populate request with data
        for field_name, field_value in request_data.items():
            if hasattr(request, field_name):
                setattr(request, field_name, field_value)
            else:
                self.logger.warning(f"Field {field_name} not found in {operation.input_message_name}")
        
        self.logger.info(f"Calling gRPC method: {operation.operation_name}")
        self.logger.debug(f"Request data: {request_data}")
        
        try:
            # Call the gRPC method
            method = getattr(stub, operation.operation_name)
            response = method(request)
            
            self.logger.info(f"gRPC call successful: {operation.operation_name}")
            return response
            
        except grpc.RpcError as e:
            self.logger.error(f"gRPC call failed: {e.code()}: {e.details()}")
            raise RuntimeError(f"gRPC call failed: {e.details()}")
        except Exception as e:
            self.logger.error(f"Unexpected error in gRPC call: {e}")
            raise