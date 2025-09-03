#!/usr/bin/env python3
"""
Docker Compose Generator for AI-Effect Onboarding Package

This script reads blueprint.json and dockerinfo.json to generate a docker-compose.yml 
file for deploying the AI-Effect pipeline services.
"""

import json
import yaml
import argparse
from pathlib import Path


class DockerComposeGenerator:
    def __init__(self, base_port=50051):
        self.base_port = base_port
        self.services = {}
        self.networks = {"ai-effect-pipeline": {"driver": "bridge"}}
        self.volumes = {"shared-data": None}
    
    def load_blueprint(self, blueprint_file):
        """Load blueprint.json and extract service information"""
        with open(blueprint_file, 'r') as f:
            blueprint = json.load(f)
        
        print(f"Loading blueprint: {blueprint.get('name', 'Unknown Pipeline')}")
        return blueprint
    
    def load_dockerinfo(self, dockerinfo_file):
        """Load dockerinfo.json and extract Docker image mappings"""
        with open(dockerinfo_file, 'r') as f:
            dockerinfo = json.load(f)
        
        return {item['container_name']: item['image_name'] 
                for item in dockerinfo['docker_image_list']}
    
    def generate_compose_service(self, node, image_mapping, port):
        """Generate docker-compose service configuration for a node"""
        container_name = node['container_name']
        image_name = image_mapping.get(container_name)
        
        if not image_name:
            print(f"Warning: No image found for container {container_name}")
            return None
        
        service = {
            'image': image_name,
            'container_name': container_name,
            'ports': [f"{port}:{port}"],
            'networks': ['ai-effect-pipeline'],
            'volumes': ['shared-data:/app/data'],
            'environment': {
                'GRPC_PORT': str(port),
                'SERVICE_NAME': container_name
            },
            'restart': 'unless-stopped'
        }
        
        return service
    
    def extract_dependencies(self, blueprint):
        """Extract service dependencies from blueprint connections"""
        dependencies = {}
        
        for node in blueprint['nodes']:
            container_name = node['container_name']
            depends_on = []
            
            # Find what services this node connects to
            for op_sig in node.get('operation_signature_list', []):
                for connection in op_sig.get('connected_to', []):
                    target_container = connection['container_name']
                    depends_on.append(target_container)
            
            if depends_on:
                dependencies[container_name] = depends_on
        
        return dependencies
    
    def generate_docker_compose(self, blueprint_file, dockerinfo_file, output_file):
        """Generate complete docker-compose.yml file"""
        
        # Load configuration files
        blueprint = self.load_blueprint(blueprint_file)
        image_mapping = self.load_dockerinfo(dockerinfo_file)
        
        # Extract service dependencies
        dependencies = self.extract_dependencies(blueprint)
        
        # Generate services
        port = self.base_port
        for node in blueprint['nodes']:
            service = self.generate_compose_service(node, image_mapping, port)
            if service:
                container_name = node['container_name']
                
                # Add dependencies
                if container_name in dependencies:
                    service['depends_on'] = dependencies[container_name]
                
                self.services[container_name] = service
                port += 1
        
        # Create complete docker-compose structure
        compose_config = {
            'version': '3.8',
            'services': self.services,
            'networks': self.networks,
            'volumes': self.volumes
        }
        
        # Write docker-compose.yml
        with open(output_file, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, indent=2)
        
        print(f"Generated docker-compose.yml with {len(self.services)} services")
        return compose_config


def main():
    parser = argparse.ArgumentParser(description='Generate Docker Compose from AI-Effect onboarding package')
    parser.add_argument('onboarding_dir', help='Path to AI-Effect onboarding export directory')
    parser.add_argument('--output', help='Output docker-compose.yml file (default: onboarding_dir/docker-compose.yml)')
    parser.add_argument('--base-port', type=int, default=50051, help='Base port for services')
    
    args = parser.parse_args()
    
    # Set up paths
    onboarding_path = Path(args.onboarding_dir)
    blueprint_file = onboarding_path / 'blueprint.json'
    dockerinfo_file = onboarding_path / 'dockerinfo.json'
    output_file = Path(args.output) if args.output else onboarding_path / 'docker-compose.yml'
    
    # Verify input files exist
    if not blueprint_file.exists():
        print(f"Error: Blueprint file {blueprint_file} not found")
        return 1
    
    if not dockerinfo_file.exists():
        print(f"Error: Docker info file {dockerinfo_file} not found")
        return 1
    
    # Generate docker-compose.yml
    generator = DockerComposeGenerator(base_port=args.base_port)
    try:
        generator.generate_docker_compose(blueprint_file, dockerinfo_file, output_file)
        
        print("\n" + "="*60)
        print("DOCKER COMPOSE USAGE")
        print("="*60)
        print(f"Generated: {output_file}")
        print(f"\n1. Start services: docker-compose -f {output_file} up -d")
        print(f"2. View logs: docker-compose -f {output_file} logs -f")
        print(f"3. Stop services: docker-compose -f {output_file} down")
        
        return 0
    except Exception as e:
        print(f"Error generating docker-compose.yml: {e}")
        return 1


if __name__ == "__main__":
    exit(main())