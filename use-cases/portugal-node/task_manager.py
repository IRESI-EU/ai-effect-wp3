"""Thread-safe task state manager for AI-Effect control interface.

Re-exports from common module for backward compatibility.
"""

from common.task_manager import TaskManager, task_manager, get_task_manager

__all__ = ["TaskManager", "task_manager", "get_task_manager"]
