"""Task dependency graph with cycle detection."""

from collections import defaultdict
from typing import Optional


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the task graph."""

    pass


class TaskGraph:
    """Directed acyclic graph for task dependencies.

    Tracks task dependencies and provides:
    - Cycle detection on add
    - Ready task queries (no pending dependencies)
    - Topological ordering
    - Failure propagation
    """

    def __init__(self):
        """Initialize empty task graph."""
        # task_id -> list of dependency task_ids
        self._dependencies: dict[str, list[str]] = {}
        # task_id -> list of dependent task_ids (reverse edges)
        self._dependents: dict[str, list[str]] = defaultdict(list)
        # Set of completed task IDs
        self._completed: set[str] = set()
        # Set of failed task IDs
        self._failed: set[str] = set()

    @property
    def task_count(self) -> int:
        """Get number of tasks in graph."""
        return len(self._dependencies)

    def add_task(self, task_id: str, dependencies: list[str]) -> None:
        """Add a task to the graph.

        Args:
            task_id: Unique task identifier.
            dependencies: List of task IDs this task depends on.

        Raises:
            CycleDetectedError: If adding this task would create a cycle.
        """
        # Check for self-dependency
        if task_id in dependencies:
            raise CycleDetectedError(f"Task '{task_id}' cannot depend on itself")

        # Temporarily add to check for cycles
        old_deps = self._dependencies.get(task_id)
        self._dependencies[task_id] = dependencies

        # Update reverse edges
        for dep_id in dependencies:
            if task_id not in self._dependents[dep_id]:
                self._dependents[dep_id].append(task_id)

        # Check for cycles using DFS
        if self._has_cycle():
            # Rollback
            if old_deps is None:
                del self._dependencies[task_id]
            else:
                self._dependencies[task_id] = old_deps
            for dep_id in dependencies:
                if task_id in self._dependents[dep_id]:
                    self._dependents[dep_id].remove(task_id)
            raise CycleDetectedError(
                f"Adding task '{task_id}' with dependencies {dependencies} would create a cycle"
            )

    def _has_cycle(self) -> bool:
        """Check if graph has a cycle using DFS.

        Returns:
            True if cycle detected.
        """
        # States: 0 = unvisited, 1 = visiting, 2 = visited
        state: dict[str, int] = defaultdict(int)

        def dfs(node: str) -> bool:
            if state[node] == 1:  # Currently visiting -> cycle
                return True
            if state[node] == 2:  # Already fully visited
                return False

            state[node] = 1  # Mark as visiting

            for dep in self._dependencies.get(node, []):
                if dfs(dep):
                    return True

            state[node] = 2  # Mark as visited
            return False

        for task_id in self._dependencies:
            if dfs(task_id):
                return True

        return False

    def get_dependencies(self, task_id: str) -> list[str]:
        """Get dependencies for a task.

        Args:
            task_id: Task to get dependencies for.

        Returns:
            List of dependency task IDs.
        """
        return self._dependencies.get(task_id, [])

    def get_dependents(self, task_id: str) -> list[str]:
        """Get tasks that depend on a given task.

        Args:
            task_id: Task to get dependents for.

        Returns:
            List of dependent task IDs.
        """
        return self._dependents.get(task_id, [])

    def get_ready_tasks(self) -> list[str]:
        """Get tasks that are ready to run.

        A task is ready if:
        - It's not completed or failed
        - All its dependencies are completed

        Returns:
            List of task IDs ready to run.
        """
        ready = []
        for task_id, deps in self._dependencies.items():
            if task_id in self._completed or task_id in self._failed:
                continue

            # Check if all dependencies are completed
            if all(dep_id in self._completed for dep_id in deps):
                ready.append(task_id)

        return ready

    def mark_completed(self, task_id: str) -> None:
        """Mark a task as completed.

        Args:
            task_id: Task that completed.
        """
        self._completed.add(task_id)

    def mark_failed(self, task_id: str) -> list[str]:
        """Mark a task as failed and determine which dependents to skip.

        For partial failure handling:
        - If a dependent has multiple parents and some succeed, don't skip
        - Only skip if ALL parents have failed

        Args:
            task_id: Task that failed.

        Returns:
            List of task IDs that should be skipped.
        """
        self._failed.add(task_id)

        to_skip: list[str] = []
        to_check = [task_id]
        checked: set[str] = set()

        while to_check:
            current = to_check.pop(0)
            if current in checked:
                continue
            checked.add(current)

            for dependent_id in self._dependents.get(current, []):
                if dependent_id in self._completed or dependent_id in self._failed:
                    continue

                # Check if ALL parents have failed
                deps = self._dependencies.get(dependent_id, [])
                all_failed = all(
                    dep_id in self._failed for dep_id in deps
                )

                if all_failed:
                    to_skip.append(dependent_id)
                    self._failed.add(dependent_id)
                    to_check.append(dependent_id)

        return to_skip

    def get_topological_order(self) -> list[str]:
        """Get tasks in topological order.

        Returns:
            List of task IDs where dependencies come before dependents.
        """
        # Kahn's algorithm
        in_degree: dict[str, int] = {tid: 0 for tid in self._dependencies}

        for task_id, deps in self._dependencies.items():
            for dep_id in deps:
                if dep_id in in_degree:
                    pass  # dep exists
                else:
                    in_degree[dep_id] = 0

        for task_id, deps in self._dependencies.items():
            in_degree[task_id] = len(deps)

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        result: list[str] = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for dependent_id in self._dependents.get(current, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        return result
