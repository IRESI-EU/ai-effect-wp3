"""Service for parsing dockerinfo.json files."""

import json
import logging
from typing import Dict, Any
from pathlib import Path


class DockerinfoService:
    """Service for handling dockerinfo.json operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_dockerinfo(self, use_case_dir: str, blueprint_nodes: list, base_port: int = 50051) -> Dict[str, Dict[str, Any]]:
        """Load network information from dockerinfo.json file.
        
        Args:
            use_case_dir: Directory containing dockerinfo.json
            blueprint_nodes: List of nodes from blueprint to determine port order
            base_port: Starting port number (default: 50051)
            
        Returns:
            Dict mapping container_name to network configuration
        """
        if not use_case_dir:
            raise ValueError("use_case_dir is required")
        
        if not blueprint_nodes:
            raise ValueError("blueprint_nodes is required")
        
        dockerinfo_file = Path(use_case_dir) / 'dockerinfo.json'
        if not dockerinfo_file.exists():
            raise FileNotFoundError(f"dockerinfo.json not found: {dockerinfo_file}")
        
        self.logger.info(f"Loading docker info from: {dockerinfo_file}")
        self.logger.info(f"Port assignment - base_port: {base_port}, nodes: {[node.container_name for node in blueprint_nodes]}")
        
        try:
            with open(dockerinfo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._parse_dockerinfo_data(data, blueprint_nodes, base_port)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dockerinfo file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load dockerinfo: {e}")
    
    def _parse_dockerinfo_data(self, data: Dict[str, Any], blueprint_nodes: list, base_port: int) -> Dict[str, Dict[str, Any]]:
        """Parse dockerinfo data into network configuration (platform format only)."""
        if 'docker_info_list' not in data:
            raise ValueError("Missing 'docker_info_list' in dockerinfo.json")

        container_configs = {}

        for item in data['docker_info_list']:
            if 'container_name' not in item:
                raise ValueError("Missing 'container_name' in docker_info_list item")

            container_name = item['container_name']
            ip_address = item.get('ip_address', 'localhost')
            port = int(item.get('port', 50051))

            network_config = {
                'address': ip_address,
                'port': port
            }

            container_configs[container_name] = network_config
            self.logger.debug(f"Configured {container_name}: {network_config}")

        return container_configs
    
