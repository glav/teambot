"""Tests for new task system commands."""

from unittest.mock import MagicMock

from teambot.repl.commands import (
    SystemCommands,
    handle_cancel,
    handle_help,
    handle_task,
    handle_tasks,
)
from teambot.tasks.models import Task, TaskResult, TaskStatus


class TestHandleHelp:
    """Tests for updated help command."""

    def test_help_includes_parallel_topic(self):
        """Test help mentions parallel topic."""
        result = handle_help([])
        assert "/help parallel" in result.output
        assert "/tasks" in result.output

    def test_help_parallel_shows_syntax(self):
        """Test /help parallel shows syntax."""
        result = handle_help(["parallel"])
        assert "&" in result.output
        assert "->" in result.output
        assert "," in result.output


class TestHandleTasks:
    """Tests for /tasks command."""

    def test_no_executor(self):
        """Test error when no executor."""
        result = handle_tasks([], None)
        assert not result.success
        assert "not available" in result.output

    def test_no_tasks(self):
        """Test when no tasks exist."""
        executor = MagicMock()
        executor.list_tasks.return_value = []

        result = handle_tasks([], executor)
        assert result.success
        assert "No tasks" in result.output

    def test_list_tasks(self):
        """Test listing tasks."""
        executor = MagicMock()
        executor.list_tasks.return_value = [
            Task(id="1", agent_id="pm", prompt="Plan the feature", status=TaskStatus.RUNNING),
            Task(id="2", agent_id="builder-1", prompt="Build it", status=TaskStatus.COMPLETED),
        ]

        result = handle_tasks([], executor)
        assert result.success
        assert "@pm" in result.output
        assert "@builder-1" in result.output
        assert "Plan the feature" in result.output
        assert "Build it" in result.output

    def test_filter_by_status(self):
        """Test filtering tasks by status."""
        executor = MagicMock()
        executor.list_tasks.return_value = [
            Task(id="1", agent_id="pm", prompt="Plan", status=TaskStatus.RUNNING),
        ]

        result = handle_tasks(["running"], executor)
        assert result.success
        executor.list_tasks.assert_called_with(status=TaskStatus.RUNNING)

    def test_invalid_status_filter(self):
        """Test invalid status filter."""
        executor = MagicMock()

        result = handle_tasks(["invalid"], executor)
        assert not result.success
        assert "Invalid status" in result.output


class TestHandleTask:
    """Tests for /task <id> command."""

    def test_no_executor(self):
        """Test error when no executor."""
        result = handle_task(["1"], None)
        assert not result.success
        assert "not available" in result.output

    def test_no_id_provided(self):
        """Test error when no ID provided."""
        executor = MagicMock()

        result = handle_task([], executor)
        assert not result.success
        assert "Usage" in result.output

    def test_task_not_found(self):
        """Test task not found."""
        executor = MagicMock()
        executor.get_task.return_value = None

        result = handle_task(["999"], executor)
        assert not result.success
        assert "not found" in result.output

    def test_show_task_details(self):
        """Test showing task details."""
        task = Task(
            id="1",
            agent_id="pm",
            prompt="Create a detailed project plan",
            status=TaskStatus.RUNNING,
            dependencies=["0"],
        )
        executor = MagicMock()
        executor.get_task.return_value = task

        result = handle_task(["1"], executor)
        assert result.success
        assert "#1" in result.output
        assert "@pm" in result.output
        assert "Create a detailed project plan" in result.output
        assert "Depends" in result.output

    def test_show_completed_result(self):
        """Test showing completed task result."""
        task = Task(
            id="1",
            agent_id="pm",
            prompt="Plan",
            status=TaskStatus.COMPLETED,
        )
        task_result = TaskResult(task_id="1", success=True, output="Here is the plan")

        executor = MagicMock()
        executor.get_task.return_value = task
        executor._manager.get_result.return_value = task_result

        result = handle_task(["1"], executor)
        assert result.success
        assert "Here is the plan" in result.output


class TestHandleCancel:
    """Tests for /cancel <id> command."""

    def test_no_executor(self):
        """Test error when no executor."""
        result = handle_cancel(["1"], None)
        assert not result.success
        assert "not available" in result.output

    def test_no_id_provided(self):
        """Test error when no ID provided."""
        executor = MagicMock()

        result = handle_cancel([], executor)
        assert not result.success
        assert "Usage" in result.output

    def test_cancel_success(self):
        """Test successful cancellation."""
        executor = MagicMock()
        executor.cancel_task.return_value = True

        result = handle_cancel(["1"], executor)
        assert result.success
        assert "Cancelled" in result.output

    def test_cancel_failure(self):
        """Test failed cancellation."""
        executor = MagicMock()
        executor.cancel_task.return_value = False

        result = handle_cancel(["999"], executor)
        assert not result.success
        assert "Could not cancel" in result.output


class TestSystemCommandsTaskIntegration:
    """Tests for SystemCommands with task executor."""

    def test_set_executor(self):
        """Test setting executor."""
        cmds = SystemCommands()
        executor = MagicMock()

        cmds.set_executor(executor)
        assert cmds._executor == executor

    def test_dispatch_tasks(self):
        """Test dispatching /tasks."""
        executor = MagicMock()
        executor.list_tasks.return_value = []

        cmds = SystemCommands(executor=executor)
        result = cmds.dispatch("tasks", [])

        assert result.success
        assert "No tasks" in result.output

    def test_dispatch_task(self):
        """Test dispatching /task."""
        task = Task(id="1", agent_id="pm", prompt="Plan", status=TaskStatus.RUNNING)
        executor = MagicMock()
        executor.get_task.return_value = task

        cmds = SystemCommands(executor=executor)
        result = cmds.dispatch("task", ["1"])

        assert result.success

    def test_dispatch_cancel(self):
        """Test dispatching /cancel."""
        executor = MagicMock()
        executor.cancel_task.return_value = True

        cmds = SystemCommands(executor=executor)
        result = cmds.dispatch("cancel", ["1"])

        assert result.success
        assert "Cancelled" in result.output
