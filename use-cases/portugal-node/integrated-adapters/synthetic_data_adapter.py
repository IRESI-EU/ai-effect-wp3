"""Synthetic Data adapter for AI-Effect orchestrator.

Usage:
    from synthetic_data_adapter import execute_handlers, create_control_router

    app.include_router(create_control_router(execute_handlers))
"""

import sys
from pathlib import Path

# Add parent directory for common module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import (
    create_control_router,
    execute_TrainModel,
    execute_GenerateData,
    synthetic_data_handlers,
)

execute_handlers = synthetic_data_handlers

__all__ = ["execute_handlers", "create_control_router", "execute_TrainModel", "execute_GenerateData"]
