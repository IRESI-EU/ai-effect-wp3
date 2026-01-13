"""Knowledge Store adapter for AI-Effect orchestrator.

Usage:
    from knowledge_store_adapter import execute_handlers, create_control_router

    app.include_router(create_control_router(execute_handlers))
"""

import sys
from pathlib import Path

# Add parent directory for common module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from common import (
    create_control_router,
    execute_ApplyFeatures,
    knowledge_store_handlers,
)

execute_handlers = knowledge_store_handlers

__all__ = ["execute_handlers", "create_control_router", "execute_ApplyFeatures"]
