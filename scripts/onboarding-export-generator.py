#!/usr/bin/env python3
"""
AI-Effect Onboarding Export Generator

This script generates an AI-Effect onboarding export package from a use case directory
containing services with their own proto files. Creates blueprint.json, dockerinfo.json,
and copies proto files in the expected format.
"""

import json
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import uuid


class OnboardingExportGenerator:
    def __init__(self, use_case_dir, output_dir):
        self.use_case_dir = Path(use_case_dir)
        self.output_dir = Path(output_dir)
        self.services_dir = self.use_case_dir / 'services'
        
    def scan_services(self):
        """Scan services directory and extract service information"""
        services = []
        
        if not self.services_dir.exists():
            raise FileNotFoundError(f"Services directory not found: {self.services_dir}")
        
        for service_dir in self.services_dir.iterdir():
            if service_dir.is_dir():
                proto_dir = service_dir / 'proto'
                if proto_dir.exists():
                    # Find proto file
                    proto_files = list(proto_dir.glob('*.proto'))
                    if proto_files:
                        service_info = {
                            'name': service_dir.name,
                            'container_name': f"{service_dir.name}1",  # Add '1' suffix like AI-Effect
                            'proto_file': proto_files[0],
                            'service_dir': service_dir
                        }
                        services.append(service_info)
                        print(f"Found service: {service_info['name']}")
                    else:
                        print(f"Warning: No proto file found in {proto_dir}")
                else:
                    print(f"Warning: No proto directory found in {service_dir}")
        
        return services
    
    def parse_proto_file(self, proto_file):
        """Parse proto file to extract service and message definitions"""
        with open(proto_file, 'r') as f:
            content = f.read()
        
        services = []
        messages = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Extract service definitions
            if line.startswith('service '):
                service_name = line.split()[1].rstrip('{')
                services.append(service_name)
            
            # Extract message definitions (for RPC inputs/outputs)
            if line.startswith('message '):
                message_name = line.split()[1].rstrip('{')
                messages.append(message_name)
            
            # Extract RPC methods
            if line.startswith('rpc '):
                # Parse: rpc MethodName(InputType) returns (OutputType);
                parts = line.replace('rpc ', '').replace(';', '').split('returns')
                if len(parts) == 2:
                    method_part = parts[0].strip()
                    return_part = parts[1].strip()
                    
                    method_name = method_part.split('(')[0].strip()
                    input_msg = method_part.split('(')[1].split(')')[0].strip()
                    output_msg = return_part.strip('()').strip()
                    
                    rpc_info = {
                        'method_name': method_name,
                        'input_message': input_msg,
                        'output_message': output_msg
                    }
                    return rpc_info
        
        return services, messages
    
    def generate_blueprint_node(self, service, connections, port):
        """Generate a blueprint node for a service"""
        
        # Extract RPC info and create operation signatures
        rpc_info = self.extract_rpc_methods(service['proto_file'])
        operation_signatures = []
        
        for rpc in rpc_info:
            operation_sig = {
                "connected_to": connections.get(service['container_name'], []),
                "operation_signature": {
                    "operation_name": rpc['method_name'],
                    "output_message_name": rpc['output_message'],
                    "input_message_name": rpc['input_message'],
                    "output_message_stream": False,
                    "input_message_stream": False
                }
            }
            operation_signatures.append(operation_sig)
        
        # Generate node
        node = {
            "proto_uri": f"microservice/{service['container_name']}.proto",
            "image": f"{self.use_case_dir.name}-{service['name'].replace('_', '-')}:latest",
            "node_type": "MLModel",
            "container_name": service['container_name'],
            "operation_signature_list": operation_signatures
        }
        
        return node
    
    def extract_rpc_methods(self, proto_file):
        """Extract RPC method information from proto file"""
        with open(proto_file, 'r') as f:
            content = f.read()
        
        rpc_methods = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('rpc '):
                # Parse: rpc MethodName(InputType) returns (OutputType);
                parts = line.replace('rpc ', '').replace(';', '').split('returns')
                if len(parts) == 2:
                    method_part = parts[0].strip()
                    return_part = parts[1].strip()
                    
                    method_name = method_part.split('(')[0].strip()
                    input_msg = method_part.split('(')[1].split(')')[0].strip()
                    output_msg = return_part.strip('()').strip()
                    
                    rpc_methods.append({
                        'method_name': method_name,
                        'input_message': input_msg,
                        'output_message': output_msg
                    })
        
        return rpc_methods
    
    def load_connections(self):
        """Load connections.json file to determine service topology"""
        connections_file = self.use_case_dir / 'connections.json'
        
        if not connections_file.exists():
            print("Warning: No connections.json found. Services will have no connections.")
            return {}
        
        with open(connections_file, 'r') as f:
            connections_config = json.load(f)
        
        return connections_config.get('pipeline', {}).get('connections', [])
    
    def create_service_connections(self, services):
        """Create service connections from connections.json"""
        connections_config = self.load_connections()
        connections = {}
        
        # Create service name to container name mapping
        service_map = {svc['name']: svc['container_name'] for svc in services}
        
        for conn in connections_config:
            from_service = conn['from_service']
            to_service = conn['to_service']
            to_method = conn['to_method']
            
            if from_service in service_map and to_service in service_map:
                from_container = service_map[from_service]
                to_container = service_map[to_service]
                
                if from_container not in connections:
                    connections[from_container] = []
                
                connections[from_container].append({
                    "container_name": to_container,
                    "operation_signature": {
                        "operation_name": to_method
                    }
                })
                
                print(f"Connection: {from_service} -> {to_service} ({to_method})")
            else:
                print(f"Warning: Connection references unknown services: {from_service} -> {to_service}")
        
        return connections
    
    def generate_blueprint(self, services):
        """Generate blueprint.json"""
        connections = self.create_service_connections(services)
        
        nodes = []
        for service in services:
            node = self.generate_blueprint_node(service, connections, 50051)
            nodes.append(node)
        
        blueprint = {
            "nodes": nodes,
            "name": f"{self.use_case_dir.name.replace('_', ' ').title()}",
            "pipeline_id": str(uuid.uuid4()),
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "type": "pipeline-topology/v2",
            "version": "2.0"
        }
        
        return blueprint
    
    def generate_dockerinfo(self, services, internal_port=50051):
        """Generate dockerinfo.json in platform format

        Note: Uses internal service port (all services listen on same internal port)
        External port mapping is handled by docker-compose.yml
        """
        docker_info_list = []

        for service in services:
            docker_info = {
                "container_name": service['container_name'],
                "ip_address": service['container_name'],  # Service name for Docker DNS
                "port": str(internal_port)  # Internal service port (all use same port)
            }
            docker_info_list.append(docker_info)

        dockerinfo = {
            "docker_info_list": docker_info_list
        }

        return dockerinfo
    
    def copy_proto_files(self, services):
        """Copy proto files to microservice directory"""
        microservice_dir = self.output_dir / 'microservice'
        microservice_dir.mkdir(parents=True, exist_ok=True)
        
        for service in services:
            src_proto = service['proto_file']
            dst_proto = microservice_dir / f"{service['container_name']}.proto"
            shutil.copy2(src_proto, dst_proto)
            print(f"Copied: {src_proto} -> {dst_proto}")
    
    def generate_metadata(self, services):
        """Generate generation_metadata.json with use case and service information"""
        metadata = {
            "use_case_name": self.use_case_dir.name,
            "use_case_directory": self.use_case_dir.name,
            "source_path": f"../../use-cases/{self.use_case_dir.name}",
            "services": []
        }

        for service in services:
            service_metadata = {
                "service_name": service['name'],
                "container_name": service['container_name'],
                "image_name": f"{self.use_case_dir.name}-{service['name'].replace('_', '-')}:latest"
            }
            metadata["services"].append(service_metadata)

        return metadata

    def generate_export(self):
        """Generate complete onboarding export"""
        print(f"Generating onboarding export from: {self.use_case_dir}")
        print(f"Output directory: {self.output_dir}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Scan services
        services = self.scan_services()
        if not services:
            raise ValueError("No services with proto files found")

        # Generate blueprint.json
        blueprint = self.generate_blueprint(services)
        blueprint_file = self.output_dir / 'blueprint.json'
        with open(blueprint_file, 'w') as f:
            json.dump(blueprint, f, indent=4)
        print(f"Generated: {blueprint_file}")

        # Generate dockerinfo.json
        dockerinfo = self.generate_dockerinfo(services)
        dockerinfo_file = self.output_dir / 'dockerinfo.json'
        with open(dockerinfo_file, 'w') as f:
            json.dump(dockerinfo, f, indent=4)
        print(f"Generated: {dockerinfo_file}")

        # Generate generation_metadata.json
        metadata = self.generate_metadata(services)
        metadata_file = self.output_dir / 'generation_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"Generated: {metadata_file}")

        # Copy proto files
        self.copy_proto_files(services)

        print(f"\nSuccessfully generated onboarding export with {len(services)} services")
        return True


def main():
    parser = argparse.ArgumentParser(description='Generate AI-Effect onboarding export from use case')
    parser.add_argument('use_case_dir', help='Path to use case directory containing services/')
    parser.add_argument('output_dir', help='Output directory for onboarding export')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing output directory')
    
    args = parser.parse_args()
    
    # Verify input directory exists
    if not Path(args.use_case_dir).exists():
        print(f"Error: Use case directory {args.use_case_dir} not found")
        return 1
    
    # Check if output directory exists
    if Path(args.output_dir).exists() and not args.overwrite:
        print(f"Error: Output directory {args.output_dir} already exists. Use --overwrite to replace it.")
        return 1
    
    # Generate export
    generator = OnboardingExportGenerator(args.use_case_dir, args.output_dir)
    try:
        generator.generate_export()
        
        print("\n" + "="*60)
        print("ONBOARDING EXPORT GENERATED")
        print("="*60)
        print(f"Location: {args.output_dir}")
        print("\nFiles created:")
        print("- blueprint.json")
        print("- dockerinfo.json")
        print("- generation_metadata.json")
        print("- microservice/*.proto")
        print(f"\nTo generate docker-compose.yml:")
        print(f"python docker-compose-generator.py {args.output_dir}")
        
        return 0
    except Exception as e:
        print(f"Error generating onboarding export: {e}")
        return 1


if __name__ == "__main__":
    exit(main())