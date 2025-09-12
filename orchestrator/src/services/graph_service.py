"""Service for building and managing execution graphs."""

import logging
from typing import Dict, List, Set

from models.node import Blueprint, Node, OperationSignatureList
from models.graph import ExecutionGraph, GraphNode


class GraphService:
    """Service for building execution graphs from blueprints."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def build_graph(self, blueprint: Blueprint) -> ExecutionGraph:
        """Build execution graph from blueprint."""
        if not blueprint:
            raise ValueError("blueprint is required")
        
        if not blueprint.nodes:
            raise ValueError("blueprint must contain at least one node")
        
        self.logger.info(f"Building execution graph for blueprint: {blueprint.name}")
        
        graph = ExecutionGraph()
        node_map = {}  # container_name:operation_name -> GraphNode
        
        # First pass: Create all GraphNodes
        for node in blueprint.nodes:
            for operation in node.operation_signature_list:
                graph_node = GraphNode(node=node, operation=operation)
                key = graph_node.key
                node_map[key] = graph_node
                graph.add_node(graph_node)
                
                self.logger.debug(f"Created graph node: {key}")
        
        # Second pass: Build connections and dependencies
        for node in blueprint.nodes:
            for operation in node.operation_signature_list:
                source_key = f"{node.container_name}:{operation.operation_signature.operation_name}"
                source_node = node_map[source_key]
                
                # Add next nodes (outgoing connections)
                for connection in operation.connected_to:
                    target_key = f"{connection.container_name}:{connection.operation_signature.operation_name}"
                    
                    if target_key not in node_map:
                        raise ValueError(f"Connection target not found: {target_key}")
                    
                    target_node = node_map[target_key]
                    source_node.next_nodes.append(target_node)
                    target_node.dependencies.append(source_node)
                    
                    self.logger.debug(f"Connected: {source_key} -> {target_key}")
        
        # Third pass: Identify start nodes (nodes with no dependencies)
        start_nodes = [node for node in graph.all_nodes.values() if not node.dependencies]
        
        if not start_nodes:
            raise ValueError("No start nodes found - circular dependency detected")
        
        graph.start_nodes = start_nodes
        
        self.logger.info(f"Graph built successfully with {len(graph.all_nodes)} nodes, "
                        f"{len(start_nodes)} start nodes")
        
        # Validate graph
        self._validate_graph(graph)
        
        return graph
    
    def _validate_graph(self, graph: ExecutionGraph):
        """Validate the execution graph."""
        self.logger.debug("Validating execution graph")
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: GraphNode) -> bool:
            visited.add(node.key)
            rec_stack.add(node.key)
            
            for next_node in node.next_nodes:
                if next_node.key not in visited:
                    if has_cycle(next_node):
                        return True
                elif next_node.key in rec_stack:
                    return True
            
            rec_stack.remove(node.key)
            return False
        
        for start_node in graph.start_nodes:
            if start_node.key not in visited:
                if has_cycle(start_node):
                    raise ValueError("Circular dependency detected in graph")
        
        # Check connectivity - all nodes should be reachable from start nodes
        reachable = set()
        
        def mark_reachable(node: GraphNode):
            if node.key in reachable:
                return
            reachable.add(node.key)
            for next_node in node.next_nodes:
                mark_reachable(next_node)
        
        for start_node in graph.start_nodes:
            mark_reachable(start_node)
        
        unreachable = set(graph.all_nodes.keys()) - reachable
        if unreachable:
            self.logger.warning(f"Unreachable nodes found: {unreachable}")
        
        self.logger.debug("Graph validation completed successfully")
    
    def get_execution_order(self, graph: ExecutionGraph) -> List[List[GraphNode]]:
        """Get topological execution order as levels (nodes that can run in parallel)."""
        if not graph:
            raise ValueError("graph is required")
        
        execution_levels = []
        remaining_nodes = set(graph.all_nodes.values())
        
        while remaining_nodes:
            # Find nodes with all dependencies satisfied
            ready_nodes = []
            for node in remaining_nodes:
                if all(dep not in remaining_nodes for dep in node.dependencies):
                    ready_nodes.append(node)
            
            if not ready_nodes:
                raise RuntimeError("Unable to determine execution order - circular dependency")
            
            execution_levels.append(ready_nodes)
            remaining_nodes -= set(ready_nodes)
        
        self.logger.info(f"Execution order determined: {len(execution_levels)} levels")
        for i, level in enumerate(execution_levels):
            node_keys = [node.key for node in level]
            self.logger.debug(f"Level {i}: {node_keys}")
        
        return execution_levels