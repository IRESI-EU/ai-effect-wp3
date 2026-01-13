"""AI-Effect Control Interface Router.

Re-exports from common module for backward compatibility.

Usage:
    from control_router import create_control_router

    app.include_router(create_control_router(execute_handlers))
"""

import sys
from pathlib import Path

# Add parent directory for common module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import (
    DataReference,
    ExecuteRequest,
    ExecuteResponse,
    StatusResponse,
    OutputResponse,
    create_control_router,
    get_task_manager,
    get_data_url,
)

__all__ = [
    "DataReference",
    "ExecuteRequest",
    "ExecuteResponse",
    "StatusResponse",
    "OutputResponse",
    "create_control_router",
    "get_task_manager",
    "get_data_url",
]
