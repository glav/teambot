"""Tasks module for parallel execution."""

from teambot.tasks.executor import ExecutionResult, TaskExecutor
from teambot.tasks.graph import CycleDetectedError, TaskGraph
from teambot.tasks.manager import TaskManager
from teambot.tasks.models import Task, TaskResult, TaskStatus
from teambot.tasks.output_injector import OutputInjector

__all__ = [
    "Task",
    "TaskResult",
    "TaskStatus",
    "TaskGraph",
    "CycleDetectedError",
    "OutputInjector",
    "TaskManager",
    "TaskExecutor",
    "ExecutionResult",
]
