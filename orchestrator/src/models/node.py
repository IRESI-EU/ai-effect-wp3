"""Data models for orchestrator nodes and operations."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class OperationSignature:
    """Represents a gRPC operation signature."""
    operation_name: str
    input_message_name: str
    output_message_name: str
    input_message_stream: bool = False
    output_message_stream: bool = False


@dataclass
class Connection:
    """Represents a connection to another node."""
    container_name: str
    operation_signature: OperationSignature


@dataclass
class OperationSignatureList:
    """Represents an operation with its connections."""
    operation_signature: OperationSignature
    connected_to: List[Connection] = field(default_factory=list)


@dataclass
class Node:
    """Represents a workflow node."""
    container_name: str
    proto_uri: str
    image: str
    node_type: str
    operation_signature_list: List[OperationSignatureList]
    
    # Runtime properties
    address: Optional[str] = None
    port: Optional[int] = None


@dataclass
class Blueprint:
    """Represents the complete workflow blueprint."""
    name: str
    pipeline_id: str
    creation_date: str
    type: str
    version: str
    nodes: List[Node]