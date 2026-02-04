"""Task models for parallel execution."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class TaskStatus(Enum):
    """Status of a task in the execution pipeline."""

    PENDING = auto()  # Waiting to run (may have unmet dependencies)
    WAITING = auto()  # Waiting for referenced agent to complete
    RUNNING = auto()  # Currently executing
    COMPLETED = auto()  # Finished successfully
    FAILED = auto()  # Finished with error
    SKIPPED = auto()  # Skipped due to parent failure
    CANCELLED = auto()  # Cancelled by user

    def is_terminal(self) -> bool:
        """Check if this is a terminal (final) status.

        Returns:
            True if task cannot transition to another state.
        """
        return self in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
            TaskStatus.CANCELLED,
        )


@dataclass
class TaskResult:
    """Result from a completed task.

    Attributes:
        task_id: ID of the task that produced this result.
        output: Output text from the task.
        success: Whether the task succeeded.
        error: Error message if failed.
        completed_at: When the task completed.
    """

    task_id: str
    output: str
    success: bool
    error: str | None = None
    completed_at: datetime = field(default_factory=datetime.now)


@dataclass
class Task:
    """A task to be executed by an agent.

    Attributes:
        id: Unique task identifier.
        agent_id: Agent to execute the task (pm, ba, etc.).
        prompt: The task prompt/instruction.
        status: Current task status.
        dependencies: List of task IDs this task depends on.
        timeout: Timeout in seconds for this task.
        background: Whether this task runs in background.
        result: Result after completion.
        started_at: When task started running.
        completed_at: When task finished.
        model: AI model to use for this task.
    """

    id: str
    agent_id: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: list[str] = field(default_factory=list)
    timeout: float = 120.0
    background: bool = False
    result: TaskResult | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model: str | None = None

    @property
    def has_dependencies(self) -> bool:
        """Check if task has dependencies.

        Returns:
            True if task depends on other tasks.
        """
        return len(self.dependencies) > 0

    def is_ready(self, completed_results: dict[str, TaskResult]) -> bool:
        """Check if task is ready to run (all dependencies satisfied).

        Args:
            completed_results: Map of task_id -> result for completed tasks.

        Returns:
            True if all dependencies are in completed_results.
        """
        if not self.has_dependencies:
            return True

        return all(dep_id in completed_results for dep_id in self.dependencies)

    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self, output: str) -> None:
        """Mark task as completed successfully.

        Args:
            output: The output from the task.
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = TaskResult(
            task_id=self.id,
            output=output,
            success=True,
            completed_at=self.completed_at,
        )

    def mark_failed(self, error: str) -> None:
        """Mark task as failed.

        Args:
            error: Error message describing the failure.
        """
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = TaskResult(
            task_id=self.id,
            output="",
            success=False,
            error=error,
            completed_at=self.completed_at,
        )

    def mark_skipped(self, reason: str) -> None:
        """Mark task as skipped.

        Args:
            reason: Reason for skipping (e.g., parent failed).
        """
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.now()
        self.result = TaskResult(
            task_id=self.id,
            output="",
            success=False,
            error=f"Skipped: {reason}",
            completed_at=self.completed_at,
        )

    def mark_cancelled(self) -> None:
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        self.result = TaskResult(
            task_id=self.id,
            output="",
            success=False,
            error="Cancelled by user",
            completed_at=self.completed_at,
        )
