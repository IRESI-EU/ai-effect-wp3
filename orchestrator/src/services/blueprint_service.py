"""Service for parsing blueprint.json files."""

import json
import logging
from typing import Dict, Any
from pathlib import Path

from models.node import Blueprint, Node, OperationSignatureList, OperationSignature, Connection


class BlueprintService:
    """Service for handling blueprint operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_blueprint(self, blueprint_path: str) -> Blueprint:
        """Load blueprint from JSON file."""
        if not blueprint_path:
            raise ValueError("blueprint_path is required")
        
        blueprint_file = Path(blueprint_path)
        if not blueprint_file.exists():
            raise FileNotFoundError(f"Blueprint file not found: {blueprint_path}")
        
        self.logger.info(f"Loading blueprint from: {blueprint_path}")
        
        try:
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._parse_blueprint_data(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in blueprint file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load blueprint: {e}")
    
    def _parse_blueprint_data(self, data: Dict[str, Any]) -> Blueprint:
        """Parse blueprint data into objects."""
        required_fields = ['name', 'pipeline_id', 'creation_date', 'type', 'version', 'nodes']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field in blueprint: {field}")
        
        nodes = []
        for node_data in data['nodes']:
            node = self._parse_node(node_data)
            nodes.append(node)
        
        return Blueprint(
            name=data['name'],
            pipeline_id=data['pipeline_id'],
            creation_date=data['creation_date'],
            type=data['type'],
            version=data['version'],
            nodes=nodes
        )
    
    def _parse_node(self, node_data: Dict[str, Any]) -> Node:
        """Parse a single node from JSON data."""
        required_fields = ['container_name', 'proto_uri', 'image', 'node_type', 'operation_signature_list']
        
        for field in required_fields:
            if field not in node_data:
                raise ValueError(f"Missing required field in node: {field}")
        
        operation_signature_list = []
        for op_data in node_data['operation_signature_list']:
            operation = self._parse_operation_signature_list(op_data)
            operation_signature_list.append(operation)
        
        return Node(
            container_name=node_data['container_name'],
            proto_uri=node_data['proto_uri'],
            image=node_data['image'],
            node_type=node_data['node_type'],
            operation_signature_list=operation_signature_list
        )
    
    def _parse_operation_signature_list(self, op_data: Dict[str, Any]) -> OperationSignatureList:
        """Parse operation signature list from JSON data."""
        required_fields = ['operation_signature', 'connected_to']
        
        for field in required_fields:
            if field not in op_data:
                raise ValueError(f"Missing required field in operation signature list: {field}")
        
        # Parse operation signature
        op_sig_data = op_data['operation_signature']
        operation_signature = self._parse_operation_signature(op_sig_data)
        
        # Parse connections
        connections = []
        for conn_data in op_data['connected_to']:
            connection = self._parse_connection(conn_data)
            connections.append(connection)
        
        return OperationSignatureList(
            operation_signature=operation_signature,
            connected_to=connections
        )
    
    def _parse_operation_signature(self, op_sig_data: Dict[str, Any]) -> OperationSignature:
        """Parse operation signature from JSON data."""
        required_fields = ['operation_name', 'input_message_name', 'output_message_name']
        
        for field in required_fields:
            if field not in op_sig_data:
                raise ValueError(f"Missing required field in operation signature: {field}")
        
        return OperationSignature(
            operation_name=op_sig_data['operation_name'],
            input_message_name=op_sig_data['input_message_name'],
            output_message_name=op_sig_data['output_message_name'],
            input_message_stream=op_sig_data.get('input_message_stream', False),
            output_message_stream=op_sig_data.get('output_message_stream', False)
        )
    
    def _parse_connection(self, conn_data: Dict[str, Any]) -> Connection:
        """Parse connection from JSON data."""
        required_fields = ['container_name', 'operation_signature']
        
        for field in required_fields:
            if field not in conn_data:
                raise ValueError(f"Missing required field in connection: {field}")
        
        # Parse operation signature (may have fewer fields than full signature)
        op_sig_data = conn_data['operation_signature']
        if 'operation_name' not in op_sig_data:
            raise ValueError("Missing operation_name in connection operation signature")
        
        operation_signature = OperationSignature(
            operation_name=op_sig_data['operation_name'],
            input_message_name=op_sig_data.get('input_message_name', ''),
            output_message_name=op_sig_data.get('output_message_name', ''),
            input_message_stream=op_sig_data.get('input_message_stream', False),
            output_message_stream=op_sig_data.get('output_message_stream', False)
        )
        
        return Connection(
            container_name=conn_data['container_name'],
            operation_signature=operation_signature
        )