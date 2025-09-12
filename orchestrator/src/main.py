"""Main entry point for the orchestrator."""

import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any

from services.log_service import configure_logging
from services.orchestration_service import OrchestrationService


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AI-Effect Workflow Orchestrator')
    
    parser.add_argument(
        'use_case_dir',
        help='Directory containing blueprint.json, proto files and other resources'
    )
    
    
    parser.add_argument(
        '--initial-data',
        type=str,
        help='JSON file or JSON string with initial data for start nodes'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def load_json_data(data_input: str) -> Dict[str, Any]:
    """Load JSON data from file or string."""
    if not data_input:
        return {}
    
    # Try to parse as file path first
    try:
        file_path = Path(data_input)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    
    # Try to parse as JSON string
    try:
        return json.loads(data_input)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}")


def validate_inputs(args):
    """Validate input arguments."""
    # Validate use case directory
    use_case_dir = Path(args.use_case_dir)
    if not use_case_dir.exists():
        raise FileNotFoundError(f"Use case directory not found: {args.use_case_dir}")
    
    if not use_case_dir.is_dir():
        raise ValueError(f"Use case path is not a directory: {args.use_case_dir}")
    
    # Validate blueprint.json exists in use case directory
    blueprint_path = use_case_dir / 'blueprint.json'
    if not blueprint_path.exists():
        raise FileNotFoundError(f"blueprint.json not found in use case directory: {blueprint_path}")
    
    if not blueprint_path.is_file():
        raise ValueError(f"blueprint.json is not a file: {blueprint_path}")


def main():
    """Main entry point."""
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Configure logging
        configure_logging()
        logger = logging.getLogger(__name__)
        
        # Set log level
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        
        logger.info("AI-Effect Workflow Orchestrator starting")
        logger.info(f"Use case directory: {args.use_case_dir}")
        
        # Blueprint path is always use_case_dir/blueprint.json
        blueprint_path = str(Path(args.use_case_dir) / 'blueprint.json')
        logger.info(f"Blueprint: {blueprint_path}")
        
        # Validate inputs
        validate_inputs(args)
        
        # Load optional data
        initial_data = load_json_data(args.initial_data) if args.initial_data else None
        
        if initial_data:
            logger.info(f"Loaded initial data: {list(initial_data.keys())}")
        
        # Create orchestration service
        orchestrator = OrchestrationService(
            use_case_dir=args.use_case_dir
        )
        
        # Execute workflow  
        results = orchestrator.execute_workflow(
            blueprint_path=blueprint_path,
            initial_data=initial_data
        )
        
        # Output results
        logger.info("Workflow execution completed successfully")
        logger.info("Execution results:")
        
        for node_key, result in results.items():
            logger.info(f"  {node_key}: {result}")
        
        # Print results to stdout as JSON for programmatic use
        print(json.dumps(results, indent=2, default=str))
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Orchestrator interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Orchestrator failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())