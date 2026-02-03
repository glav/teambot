"""Tests for Task dataclass and TaskStatus."""

from datetime import datetime

from teambot.tasks.models import Task, TaskResult, TaskStatus


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values_exist(self):
        """Test all required status values exist."""
        assert TaskStatus.PENDING
        assert TaskStatus.RUNNING
        assert TaskStatus.COMPLETED
        assert TaskStatus.FAILED
        assert TaskStatus.SKIPPED
        assert TaskStatus.CANCELLED

    def test_status_is_terminal(self):
        """Test terminal status detection."""
        assert TaskStatus.COMPLETED.is_terminal()
        assert TaskStatus.FAILED.is_terminal()
        assert TaskStatus.SKIPPED.is_terminal()
        assert TaskStatus.CANCELLED.is_terminal()
        assert not TaskStatus.PENDING.is_terminal()
        assert not TaskStatus.RUNNING.is_terminal()


class TestTask:
    """Tests for Task dataclass."""

    def test_task_creation_minimal(self):
        """Test creating task with minimal fields."""
        task = Task(
            id="task-1",
            agent_id="pm",
            prompt="Create a plan",
        )

        assert task.id == "task-1"
        assert task.agent_id == "pm"
        assert task.prompt == "Create a plan"
        assert task.status == TaskStatus.PENDING
        assert task.dependencies == []
        assert task.timeout == 120.0
        assert task.result is None

    def test_task_creation_full(self):
        """Test creating task with all fields."""
        task = Task(
            id="task-2",
            agent_id="builder-1",
            prompt="Implement feature",
            dependencies=["task-1"],
            timeout=60.0,
            background=True,
        )

        assert task.id == "task-2"
        assert task.dependencies == ["task-1"]
        assert task.timeout == 60.0
        assert task.background is True

    def test_task_has_dependencies(self):
        """Test has_dependencies property."""
        task_no_deps = Task(id="t1", agent_id="pm", prompt="test")
        task_with_deps = Task(id="t2", agent_id="pm", prompt="test", dependencies=["t1"])

        assert not task_no_deps.has_dependencies
        assert task_with_deps.has_dependencies

    def test_task_is_ready_no_deps(self):
        """Test is_ready when no dependencies."""
        task = Task(id="t1", agent_id="pm", prompt="test")
        completed_tasks = {}

        assert task.is_ready(completed_tasks)

    def test_task_is_ready_deps_completed(self):
        """Test is_ready when dependencies completed."""
        task = Task(id="t2", agent_id="pm", prompt="test", dependencies=["t1"])
        completed_tasks = {"t1": TaskResult(task_id="t1", output="done", success=True)}

        assert task.is_ready(completed_tasks)

    def test_task_is_ready_deps_not_completed(self):
        """Test is_ready when dependencies not completed."""
        task = Task(id="t2", agent_id="pm", prompt="test", dependencies=["t1"])
        completed_tasks = {}

        assert not task.is_ready(completed_tasks)

    def test_task_is_ready_partial_deps(self):
        """Test is_ready when some dependencies completed."""
        task = Task(id="t3", agent_id="pm", prompt="test", dependencies=["t1", "t2"])
        completed_tasks = {"t1": TaskResult(task_id="t1", output="done", success=True)}

        assert not task.is_ready(completed_tasks)

    def test_task_mark_running(self):
        """Test marking task as running."""
        task = Task(id="t1", agent_id="pm", prompt="test")
        task.mark_running()

        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_task_mark_completed(self):
        """Test marking task as completed."""
        task = Task(id="t1", agent_id="pm", prompt="test")
        task.mark_running()
        task.mark_completed("Result output")

        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None
        assert task.result.output == "Result output"
        assert task.result.success is True
        assert task.completed_at is not None

    def test_task_mark_failed(self):
        """Test marking task as failed."""
        task = Task(id="t1", agent_id="pm", prompt="test")
        task.mark_running()
        task.mark_failed("Timeout error")

        assert task.status == TaskStatus.FAILED
        assert task.result is not None
        assert task.result.success is False
        assert task.result.error == "Timeout error"

    def test_task_mark_skipped(self):
        """Test marking task as skipped."""
        task = Task(id="t2", agent_id="pm", prompt="test", dependencies=["t1"])
        task.mark_skipped("Parent task failed")

        assert task.status == TaskStatus.SKIPPED
        assert task.result is not None
        assert task.result.success is False
        assert "Parent task failed" in task.result.error


class TestTaskResult:
    """Tests for TaskResult dataclass."""

    def test_result_success(self):
        """Test successful result."""
        result = TaskResult(task_id="t1", output="Hello", success=True)

        assert result.task_id == "t1"
        assert result.output == "Hello"
        assert result.success is True
        assert result.error is None

    def test_result_failure(self):
        """Test failed result."""
        result = TaskResult(task_id="t1", output="", success=False, error="Timeout")

        assert result.success is False
        assert result.error == "Timeout"

    def test_result_timestamp(self):
        """Test result has timestamp."""
        result = TaskResult(task_id="t1", output="test", success=True)

        assert result.completed_at is not None
        assert isinstance(result.completed_at, datetime)
