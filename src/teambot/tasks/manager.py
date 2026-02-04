"""Task manager for parallel execution."""

import asyncio
import uuid
from collections.abc import Awaitable, Callable

from teambot.tasks.graph import TaskGraph
from teambot.tasks.models import Task, TaskResult, TaskStatus
from teambot.tasks.output_injector import OutputInjector

# Type for the executor function
ExecutorFn = Callable[[str, str], Awaitable[str]]


class TaskManager:
    """Manages task execution with dependencies and concurrency control.

    Provides:
    - Task creation and tracking
    - Dependency-aware execution
    - Concurrency limiting
    - Output injection between dependent tasks
    """

    def __init__(
        self,
        executor: ExecutorFn | None = None,
        max_concurrent: int = 3,
        default_timeout: float = 120.0,
    ):
        """Initialize task manager.

        Args:
            executor: Async function(agent_id, prompt) -> output.
            max_concurrent: Maximum concurrent tasks.
            default_timeout: Default timeout for tasks in seconds.
        """
        self._executor = executor
        self._max_concurrent = max_concurrent
        self._default_timeout = default_timeout

        self._tasks: dict[str, Task] = {}
        self._graph = TaskGraph()
        self._injector = OutputInjector()
        self._results: dict[str, TaskResult] = {}
        self._agent_results: dict[str, TaskResult] = {}  # agent_id -> latest result

        # Semaphore for concurrency control
        self._semaphore: asyncio.Semaphore | None = None

    @property
    def max_concurrent(self) -> int:
        """Get max concurrent tasks."""
        return self._max_concurrent

    @property
    def task_count(self) -> int:
        """Get total number of tasks."""
        return len(self._tasks)

    def create_task(
        self,
        agent_id: str,
        prompt: str,
        dependencies: list[str] | None = None,
        timeout: float | None = None,
        background: bool = False,
    ) -> Task:
        """Create a new task.

        Args:
            agent_id: Agent to execute the task.
            prompt: Task prompt.
            dependencies: List of task IDs this task depends on.
            timeout: Timeout in seconds (uses default if not specified).
            background: Whether task runs in background.

        Returns:
            Created Task object.
        """
        task_id = f"task-{agent_id}-{uuid.uuid4().hex[:8]}"
        deps = dependencies or []

        task = Task(
            id=task_id,
            agent_id=agent_id,
            prompt=prompt,
            dependencies=deps,
            timeout=timeout or self._default_timeout,
            background=background,
        )

        self._tasks[task_id] = task
        self._graph.add_task(task_id, deps)

        return task

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """List tasks, optionally filtered by status.

        Args:
            status: Filter by this status (None for all).

        Returns:
            List of tasks.
        """
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        return tasks

    async def execute_task(self, task_id: str) -> TaskResult:
        """Execute a single task.

        Args:
            task_id: Task to execute.

        Returns:
            Task result.
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        if self._executor is None:
            raise ValueError("No executor configured")

        # Build prompt with injected parent outputs
        prompt = self._build_prompt(task)

        task.mark_running()

        try:
            output = await self._executor(task.agent_id, prompt)
            task.mark_completed(output)
            self._results[task_id] = task.result
            self._agent_results[task.agent_id] = task.result  # Store by agent_id
            self._graph.mark_completed(task_id)
        except Exception as e:
            task.mark_failed(str(e))
            self._results[task_id] = task.result
            self._agent_results[task.agent_id] = task.result  # Store failed result too
            # Mark dependents to skip
            to_skip = self._graph.mark_failed(task_id)
            for skip_id in to_skip:
                skip_task = self._tasks.get(skip_id)
                if skip_task:
                    skip_task.mark_skipped(f"Parent task {task_id} failed")
                    self._results[skip_id] = skip_task.result

        return task.result

    def _build_prompt(self, task: Task) -> str:
        """Build prompt with injected parent outputs.

        Args:
            task: Task to build prompt for.

        Returns:
            Prompt with parent outputs injected.
        """
        if not task.dependencies:
            return task.prompt

        # Build agent map for nicer headers
        agent_map = {
            tid: self._tasks[tid].agent_id for tid in task.dependencies if tid in self._tasks
        }

        return self._injector.inject(
            task.prompt,
            self._results,
            task.dependencies,
            agent_map=agent_map,
        )

    async def execute_all(self) -> list[TaskResult]:
        """Execute all tasks respecting dependencies and concurrency.

        Returns:
            List of all task results.
        """
        if self._executor is None:
            raise ValueError("No executor configured")

        self._semaphore = asyncio.Semaphore(self._max_concurrent)

        # Get execution order
        order = self._graph.get_topological_order()

        # Group tasks by dependency level for parallel execution
        results: list[TaskResult] = []

        # Simple sequential execution respecting dependencies
        # TODO: Optimize with parallel execution of independent tasks
        for task_id in order:
            task = self._tasks.get(task_id)
            if not task:
                continue

            # Skip already completed/failed/skipped
            if task.status.is_terminal():
                if task.result:
                    results.append(task.result)
                continue

            # Wait for dependencies
            if not task.is_ready(self._results):
                # Check if should be skipped due to failed deps
                deps_failed = all(
                    self._results.get(d) and not self._results[d].success for d in task.dependencies
                )
                if deps_failed:
                    task.mark_skipped("All parent tasks failed")
                    self._results[task_id] = task.result
                    results.append(task.result)
                    continue

            async with self._semaphore:
                result = await self.execute_task(task_id)
                results.append(result)

        return results

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task if possible.

        Args:
            task_id: Task to cancel.

        Returns:
            True if cancelled, False if cannot cancel.
        """
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status.is_terminal():
            return False

        task.mark_cancelled()
        self._results[task_id] = task.result
        return True

    def get_result(self, task_id: str) -> TaskResult | None:
        """Get result for a completed task.

        Args:
            task_id: Task identifier.

        Returns:
            TaskResult if available.
        """
        return self._results.get(task_id)

    def get_agent_result(self, agent_id: str) -> TaskResult | None:
        """Get latest result for an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Latest TaskResult for agent, or None.
        """
        return self._agent_results.get(agent_id)

    def get_running_task_for_agent(self, agent_id: str) -> Task | None:
        """Get currently running task for an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Running Task if found, else None.
        """
        for task in self._tasks.values():
            if task.agent_id == agent_id and task.status == TaskStatus.RUNNING:
                return task
        return None
