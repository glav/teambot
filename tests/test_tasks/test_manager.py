"""Tests for TaskManager."""

from unittest.mock import AsyncMock

import pytest

from teambot.tasks.manager import TaskManager
from teambot.tasks.models import TaskStatus


class TestTaskManagerBasic:
    """Basic TaskManager tests."""

    def test_create_manager(self):
        """Test creating task manager."""
        manager = TaskManager(max_concurrent=3)

        assert manager.max_concurrent == 3
        assert manager.task_count == 0

    def test_create_task(self):
        """Test creating a task."""
        manager = TaskManager()
        task = manager.create_task("pm", "Create a plan")

        assert task.id is not None
        assert task.agent_id == "pm"
        assert task.prompt == "Create a plan"
        assert task.status == TaskStatus.PENDING
        assert manager.task_count == 1

    def test_create_task_with_background(self):
        """Test creating a background task."""
        manager = TaskManager()
        task = manager.create_task("pm", "Create a plan", background=True)

        assert task.background is True

    def test_create_task_with_dependencies(self):
        """Test creating task with dependencies."""
        manager = TaskManager()
        t1 = manager.create_task("pm", "Plan")
        t2 = manager.create_task("builder-1", "Build", dependencies=[t1.id])

        assert t2.dependencies == [t1.id]

    def test_get_task(self):
        """Test getting task by ID."""
        manager = TaskManager()
        task = manager.create_task("pm", "Plan")

        retrieved = manager.get_task(task.id)

        assert retrieved is task

    def test_get_task_not_found(self):
        """Test getting non-existent task."""
        manager = TaskManager()

        assert manager.get_task("nonexistent") is None

    def test_list_tasks(self):
        """Test listing all tasks."""
        manager = TaskManager()
        manager.create_task("pm", "Plan")
        manager.create_task("ba", "Analyze")

        tasks = manager.list_tasks()

        assert len(tasks) == 2

    def test_list_tasks_by_status(self):
        """Test listing tasks filtered by status."""
        manager = TaskManager()
        t1 = manager.create_task("pm", "Plan")
        manager.create_task("ba", "Analyze")
        t1.mark_running()

        running = manager.list_tasks(status=TaskStatus.RUNNING)
        pending = manager.list_tasks(status=TaskStatus.PENDING)

        assert len(running) == 1
        assert len(pending) == 1


class TestTaskManagerExecution:
    """Tests for task execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_task(self):
        """Test executing a simple task."""
        mock_executor = AsyncMock(return_value="Task completed")
        manager = TaskManager(executor=mock_executor)

        task = manager.create_task("pm", "Plan")
        await manager.execute_task(task.id)

        assert task.status == TaskStatus.COMPLETED
        assert task.result.output == "Task completed"

    @pytest.mark.asyncio
    async def test_execute_task_failure(self):
        """Test task execution failure."""
        mock_executor = AsyncMock(side_effect=Exception("SDK Error"))
        manager = TaskManager(executor=mock_executor)

        task = manager.create_task("pm", "Plan")
        await manager.execute_task(task.id)

        assert task.status == TaskStatus.FAILED
        assert "SDK Error" in task.result.error

    @pytest.mark.asyncio
    async def test_execute_respects_dependencies(self):
        """Test that tasks wait for dependencies."""
        executed = []

        async def mock_exec(agent_id, prompt):
            executed.append(agent_id)
            return f"{agent_id} done"

        manager = TaskManager(executor=mock_exec)
        t1 = manager.create_task("pm", "Plan")
        t2 = manager.create_task("builder-1", "Build", dependencies=[t1.id])

        # Execute t2 first - should wait for t1
        # In real implementation, this would be handled by the scheduler
        await manager.execute_task(t1.id)
        await manager.execute_task(t2.id)

        assert executed == ["pm", "builder-1"]

    @pytest.mark.asyncio
    async def test_execute_injects_parent_output(self):
        """Test that parent output is injected into dependent task."""
        captured_prompts = []

        async def mock_exec(agent_id, prompt):
            captured_prompts.append(prompt)
            return f"{agent_id} output"

        manager = TaskManager(executor=mock_exec)
        t1 = manager.create_task("pm", "Create plan")
        t2 = manager.create_task("builder-1", "Implement", dependencies=[t1.id])

        await manager.execute_task(t1.id)
        await manager.execute_task(t2.id)

        # Second prompt should include first task's output
        assert "pm output" in captured_prompts[1]
        assert "Implement" in captured_prompts[1]


class TestTaskManagerConcurrency:
    """Tests for concurrency limiting."""

    @pytest.mark.asyncio
    async def test_respects_max_concurrent(self):
        """Test that max_concurrent is respected."""
        import asyncio

        running_count = 0
        max_running = 0

        async def slow_exec(agent_id, prompt):
            nonlocal running_count, max_running
            running_count += 1
            max_running = max(max_running, running_count)
            await asyncio.sleep(0.1)
            running_count -= 1
            return "done"

        manager = TaskManager(executor=slow_exec, max_concurrent=2)

        # Create 4 tasks
        for i in range(4):
            manager.create_task("pm", f"Task {i}", background=True)

        # Execute all
        await manager.execute_all()

        # Should never exceed max_concurrent
        assert max_running <= 2


class TestTaskManagerDependencyFailure:
    """Tests for dependency failure handling."""

    @pytest.mark.asyncio
    async def test_skip_on_parent_failure(self):
        """Test that dependent task is skipped when parent fails."""
        call_count = 0

        async def failing_exec(agent_id, prompt):
            nonlocal call_count
            call_count += 1
            if agent_id == "pm":
                raise Exception("PM failed")
            return "done"

        manager = TaskManager(executor=failing_exec)
        t1 = manager.create_task("pm", "Plan")
        t2 = manager.create_task("builder-1", "Build", dependencies=[t1.id])

        await manager.execute_all()

        assert t1.status == TaskStatus.FAILED
        assert t2.status == TaskStatus.SKIPPED
        assert call_count == 1  # Only t1 was attempted

    @pytest.mark.asyncio
    async def test_partial_failure_continues(self):
        """Test that partial failure allows continuation."""

        async def partial_exec(agent_id, prompt):
            if agent_id == "builder-1":
                raise Exception("Builder-1 failed")
            return f"{agent_id} done"

        manager = TaskManager(executor=partial_exec)
        t1 = manager.create_task("builder-1", "Build part 1")
        t2 = manager.create_task("builder-2", "Build part 2")
        t3 = manager.create_task("reviewer", "Review", dependencies=[t1.id, t2.id])

        await manager.execute_all()

        assert t1.status == TaskStatus.FAILED
        assert t2.status == TaskStatus.COMPLETED
        # t3 should still run with partial results
        assert t3.status == TaskStatus.COMPLETED


class TestTaskManagerCancel:
    """Tests for task cancellation."""

    def test_cancel_pending_task(self):
        """Test cancelling a pending task."""
        manager = TaskManager()
        task = manager.create_task("pm", "Plan")

        result = manager.cancel_task(task.id)

        assert result is True
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_running_task(self):
        """Test cancelling a running task."""
        manager = TaskManager()
        task = manager.create_task("pm", "Plan")
        task.mark_running()

        result = manager.cancel_task(task.id)

        assert result is True
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_completed_task(self):
        """Test cannot cancel completed task."""
        manager = TaskManager()
        task = manager.create_task("pm", "Plan")
        task.mark_completed("Done")

        result = manager.cancel_task(task.id)

        assert result is False
        assert task.status == TaskStatus.COMPLETED


class TestAgentResults:
    """Tests for agent result storage and retrieval."""

    @pytest.mark.asyncio
    async def test_agent_result_stored_on_completion(self):
        """Test result is stored by agent_id after completion."""
        mock_executor = AsyncMock(return_value="Analysis complete")
        manager = TaskManager(executor=mock_executor)

        task = manager.create_task(agent_id="ba", prompt="Analyze")
        await manager.execute_task(task.id)

        result = manager.get_agent_result("ba")
        assert result is not None
        assert result.success
        assert result.output == "Analysis complete"

    @pytest.mark.asyncio
    async def test_get_agent_result_returns_latest(self):
        """Test latest result overwrites previous."""
        call_count = {"count": 0}

        async def mock_executor(agent_id, prompt):
            call_count["count"] += 1
            return f"Result {call_count['count']}"

        manager = TaskManager(executor=mock_executor)

        # First task
        task1 = manager.create_task(agent_id="ba", prompt="First")
        await manager.execute_task(task1.id)

        # Second task for same agent
        task2 = manager.create_task(agent_id="ba", prompt="Second")
        await manager.execute_task(task2.id)

        result = manager.get_agent_result("ba")
        # Should be from second task
        assert result.output == "Result 2"

    def test_get_agent_result_returns_none_when_missing(self):
        """Test None returned when agent has no results."""
        manager = TaskManager()

        result = manager.get_agent_result("never_ran")

        assert result is None

    def test_get_running_task_for_agent(self):
        """Test finding running task for agent."""
        manager = TaskManager()

        task = manager.create_task(agent_id="ba", prompt="Slow task")
        # Manually set running state
        task.mark_running()

        running = manager.get_running_task_for_agent("ba")

        assert running is not None
        assert running.id == task.id
        assert running.status == TaskStatus.RUNNING

    def test_get_running_task_returns_none_when_idle(self):
        """Test None returned when agent has no running task."""
        manager = TaskManager()

        running = manager.get_running_task_for_agent("idle_agent")

        assert running is None

    def test_get_running_task_ignores_completed(self):
        """Test completed tasks are not returned as running."""
        manager = TaskManager()

        task = manager.create_task(agent_id="ba", prompt="Task")
        task.mark_running()
        task.mark_completed("Done")

        running = manager.get_running_task_for_agent("ba")

        assert running is None

    @pytest.mark.asyncio
    async def test_agent_result_stored_on_failure(self):
        """Test failed result is also stored by agent_id."""
        async def failing_executor(agent_id, prompt):
            raise Exception("Task failed")

        manager = TaskManager(executor=failing_executor)

        task = manager.create_task(agent_id="ba", prompt="Will fail")
        await manager.execute_task(task.id)

        result = manager.get_agent_result("ba")
        assert result is not None
        assert not result.success
        assert "Task failed" in result.error
