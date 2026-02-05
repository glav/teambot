"""Task executor - bridges REPL commands to TaskManager."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from teambot.repl.parser import Command, CommandType
from teambot.tasks.manager import TaskManager
from teambot.tasks.models import Task, TaskStatus

if TYPE_CHECKING:
    from teambot.ui.agent_state import AgentStatusManager

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result from executing a command.

    Attributes:
        success: Whether execution succeeded.
        output: Combined output text.
        task_id: ID of single task (for simple commands).
        task_ids: IDs of all tasks (for multi-agent/pipeline).
        background: Whether tasks are running in background.
        error: Error message if failed.
    """

    success: bool
    output: str
    task_id: str | None = None
    task_ids: list[str] = field(default_factory=list)
    background: bool = False
    error: str | None = None


class TaskExecutor:
    """Executes REPL commands using TaskManager.

    Bridges the gap between parsed commands and task execution,
    handling:
    - Simple agent commands
    - Background execution (&)
    - Multi-agent fan-out (,)
    - Pipelines with dependencies (->)
    """

    def __init__(
        self,
        sdk_client,
        max_concurrent: int = 3,
        default_timeout: float = 120.0,
        on_task_complete: Callable | None = None,
        on_task_started: Callable | None = None,
        on_streaming_chunk: Callable | None = None,
        on_stage_change: Callable | None = None,
        on_stage_output: Callable | None = None,
        on_pipeline_complete: Callable | None = None,
        agent_status_manager: AgentStatusManager | None = None,
    ):
        """Initialize executor.

        Args:
            sdk_client: Copilot SDK client for agent execution.
            max_concurrent: Maximum concurrent tasks.
            default_timeout: Default task timeout in seconds.
            on_task_complete: Callback when task completes (for notifications).
            on_task_started: Callback when task starts (for overlay updates).
            on_streaming_chunk: Callback for streaming chunks (agent_id, chunk).
            on_stage_change: Callback when pipeline stage changes (stage, total, agents).
            on_stage_output: Callback for intermediate output (agent_id, output).
            on_pipeline_complete: Callback when pipeline completes (clears progress).
            agent_status_manager: Optional manager for agent status updates.
        """
        self._sdk_client = sdk_client
        self._on_task_complete = on_task_complete
        self._on_task_started = on_task_started
        self._on_streaming_chunk = on_streaming_chunk
        self._on_stage_change = on_stage_change
        self._on_stage_output = on_stage_output
        self._on_pipeline_complete = on_pipeline_complete
        self._agent_status = agent_status_manager

        # Create manager with our executor function
        self._manager = TaskManager(
            executor=self._execute_agent_task,
            max_concurrent=max_concurrent,
            default_timeout=default_timeout,
        )

        # Track background task futures
        self._background_tasks: dict[str, asyncio.Task] = {}

    @property
    def task_count(self) -> int:
        """Get total number of tasks."""
        return self._manager.task_count

    def set_agent_status_manager(self, manager: AgentStatusManager) -> None:
        """Set the agent status manager for status updates.

        Args:
            manager: AgentStatusManager instance.
        """
        self._agent_status = manager

    def _status_running(self, agent_id: str, task_desc: str) -> None:
        """Mark agent as running in status manager."""
        if self._agent_status:
            self._agent_status.set_running(agent_id, task_desc)

    def _status_completed(self, agent_id: str) -> None:
        """Mark agent as completed in status manager."""
        if self._agent_status:
            self._agent_status.set_completed(agent_id)

    def _status_failed(self, agent_id: str) -> None:
        """Mark agent as failed in status manager."""
        if self._agent_status:
            self._agent_status.set_failed(agent_id)

    def _status_idle(self, agent_id: str) -> None:
        """Mark agent as idle in status manager."""
        if self._agent_status:
            self._agent_status.set_idle(agent_id)

    async def _execute_agent_task(
        self, agent_id: str, prompt: str, model: str | None = None
    ) -> str:
        """Execute a task via SDK.

        Args:
            agent_id: Agent to execute task.
            prompt: Task prompt (already includes persona context).
            model: Optional model to use for this task.

        Returns:
            Output from agent.
        """
        # Check if SDK client supports streaming
        if hasattr(self._sdk_client, "execute_streaming") and self._on_streaming_chunk:
            # Use streaming with callback
            def on_chunk(chunk: str):
                self._on_streaming_chunk(agent_id, chunk)

            # First ensure session is created with the model
            if model:
                await self._sdk_client.get_or_create_session(agent_id, model=model)
            return await self._sdk_client.execute_streaming(agent_id, prompt, on_chunk)
        else:
            # Fall back to regular execute
            if model:
                await self._sdk_client.get_or_create_session(agent_id, model=model)
            return await self._sdk_client.execute(agent_id, prompt)

    async def execute(self, command: Command) -> ExecutionResult:
        """Execute a parsed command.

        Args:
            command: Parsed command from REPL.

        Returns:
            ExecutionResult with output and status.
        """
        if command.type != CommandType.AGENT:
            return ExecutionResult(
                success=False,
                output="",
                error="Not an agent command",
            )

        if command.is_pipeline:
            return await self._execute_pipeline(command)
        elif len(command.agent_ids) > 1:
            return await self._execute_multiagent(command)
        else:
            return await self._execute_simple(command)

    async def _execute_simple(self, command: Command) -> ExecutionResult:
        """Execute simple single-agent command.

        Args:
            command: Parsed command.

        Returns:
            ExecutionResult.
        """
        agent_id = command.agent_ids[0]

        # Check for $ref dependencies
        if command.references:
            # Validate all referenced agents exist
            from teambot.repl.router import VALID_AGENTS

            invalid_refs = [ref for ref in command.references if ref not in VALID_AGENTS]
            if invalid_refs:
                valid_list = ", ".join(sorted(VALID_AGENTS))
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Unknown agent ref: ${invalid_refs[0]}. Valid: {valid_list}",
                )

            # Wait for any referenced agents that are currently running
            await self._wait_for_references(command.references)

            # Build prompt with injected outputs
            prompt = self._inject_references(command.content, command.references)
        else:
            prompt = command.content

        # Custom agents in .github/agents/ handle persona context
        task = self._manager.create_task(
            agent_id=agent_id,
            prompt=prompt,
            background=command.background,
            model=command.model,
        )

        if command.background:
            # Start in background and return immediately
            bg_task = asyncio.create_task(self._run_task_with_callback(task.id))
            self._background_tasks[task.id] = bg_task

            return ExecutionResult(
                success=True,
                output=f"Task #{task.id} started in background",
                task_id=task.id,
                task_ids=[task.id],
                background=True,
            )
        else:
            # Execute synchronously
            if self._on_task_started:
                self._on_task_started(task)
            self._status_running(agent_id, prompt[:40] if prompt else "")
            try:
                result = await self._manager.execute_task(task.id)
                if result.success:
                    self._status_completed(agent_id)
                else:
                    self._status_failed(agent_id)
            except asyncio.CancelledError:
                self._status_failed(agent_id)
                raise
            finally:
                self._status_idle(agent_id)
            if self._on_task_complete:
                self._on_task_complete(task, self._manager.get_result(task.id))
            return ExecutionResult(
                success=result.success,
                output=result.output if result.success else f"Error: {result.error}",
                task_id=task.id,
                task_ids=[task.id],
                error=result.error if not result.success else None,
            )

    async def _wait_for_references(self, references: list[str]) -> None:
        """Wait for referenced agents to complete any running tasks.

        Args:
            references: List of agent IDs to wait for.
        """
        for agent_id in references:
            running_task = self._manager.get_running_task_for_agent(agent_id)
            if running_task:
                # Wait for the task to complete
                while running_task.status == TaskStatus.RUNNING:
                    await asyncio.sleep(0.1)

    def _inject_references(self, prompt: str, references: list[str]) -> str:
        """Inject referenced agent outputs into prompt.

        Args:
            prompt: Original prompt with $ref tokens.
            references: List of agent IDs referenced.

        Returns:
            Prompt with outputs prepended.
        """
        sections = []
        for agent_id in references:
            result = self._manager.get_agent_result(agent_id)
            if result and result.success:
                sections.append(f"=== Output from @{agent_id} ===\n{result.output}\n")
            else:
                sections.append(f"=== Output from @{agent_id} ===\n[No output available]\n")

        sections.append(f"=== Your Task ===\n{prompt}")
        return "\n".join(sections)

    async def _execute_multiagent(self, command: Command) -> ExecutionResult:
        """Execute multi-agent fan-out command.

        Args:
            command: Parsed command with multiple agents.

        Returns:
            ExecutionResult with combined outputs.
        """
        tasks = []
        for agent_id in command.agent_ids:
            # Custom agents in .github/agents/ handle persona context
            task = self._manager.create_task(
                agent_id=agent_id,
                prompt=command.content,
                background=command.background,
                model=command.model,
            )
            tasks.append(task)

        task_ids = [t.id for t in tasks]

        if command.background:
            # Start all in background
            for task in tasks:
                bg_task = asyncio.create_task(self._run_task_with_callback(task.id))
                self._background_tasks[task.id] = bg_task

            return ExecutionResult(
                success=True,
                output=f"Tasks started in background: {', '.join(task_ids)}",
                task_ids=task_ids,
                background=True,
            )
        else:
            # Notify task started and mark all agents as running before parallel execution
            for task in tasks:
                if self._on_task_started:
                    self._on_task_started(task)
                self._status_running(task.agent_id, command.content[:40] if command.content else "")

            try:
                # Execute all in parallel and wait
                await asyncio.gather(
                    *[self._manager.execute_task(t.id) for t in tasks],
                    return_exceptions=True,
                )

                # Collect results and update status
                outputs = []
                all_success = True
                errors = []

                for task in tasks:
                    result = self._manager.get_result(task.id)
                    if result:
                        if result.success:
                            self._status_completed(task.agent_id)
                            outputs.append(f"=== @{task.agent_id} ===\n{result.output}")
                        else:
                            self._status_failed(task.agent_id)
                            all_success = False
                            errors.append(f"@{task.agent_id}: {result.error}")
                            outputs.append(f"=== @{task.agent_id} ===\n[Failed: {result.error}]")

                        # Notify task complete
                        if self._on_task_complete:
                            self._on_task_complete(task, result)
            except asyncio.CancelledError:
                for task in tasks:
                    self._status_failed(task.agent_id)
                raise
            finally:
                # Mark all agents as idle
                for task in tasks:
                    self._status_idle(task.agent_id)

            return ExecutionResult(
                success=all_success,
                output="\n\n".join(outputs),
                task_ids=task_ids,
                error="; ".join(errors) if errors else None,
            )

    async def _execute_pipeline(self, command: Command) -> ExecutionResult:
        """Execute pipeline command.

        Args:
            command: Parsed command with pipeline stages.

        Returns:
            ExecutionResult.
        """
        if not command.pipeline:
            return ExecutionResult(success=False, output="", error="Empty pipeline")

        # Handle $ref dependencies for the first stage
        if command.references:
            # Validate all referenced agents exist
            from teambot.repl.router import VALID_AGENTS

            invalid_refs = [ref for ref in command.references if ref not in VALID_AGENTS]
            if invalid_refs:
                valid_list = ", ".join(sorted(VALID_AGENTS))
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Unknown agent ref: ${invalid_refs[0]}. Valid: {valid_list}",
                )
            await self._wait_for_references(command.references)

        all_task_ids: list[str] = []
        previous_task_ids: list[str] = []
        stage_task_map: dict[int, list[str]] = {}  # stage_index -> task_ids

        # Create tasks for each stage with dependencies
        for i, stage in enumerate(command.pipeline):
            stage_task_ids = []

            for agent_id in stage.agent_ids:
                # For first stage, inject references if any
                if i == 0 and command.references:
                    prompt = self._inject_references(stage.content, command.references)
                else:
                    prompt = stage.content

                # Custom agents in .github/agents/ handle persona context
                task = self._manager.create_task(
                    agent_id=agent_id,
                    prompt=prompt,
                    dependencies=previous_task_ids.copy(),
                    background=command.background,
                    model=command.model,
                )
                stage_task_ids.append(task.id)
                all_task_ids.append(task.id)

            stage_task_map[i] = stage_task_ids
            previous_task_ids = stage_task_ids

        total_stages = len(command.pipeline)

        if command.background:
            # Start pipeline in background
            bg_task = asyncio.create_task(
                self._run_pipeline_with_callback(all_task_ids, stage_task_map, total_stages)
            )
            for task_id in all_task_ids:
                self._background_tasks[task_id] = bg_task

            return ExecutionResult(
                success=True,
                output=f"Pipeline started in background ({total_stages} stages)",
                task_ids=all_task_ids,
                background=True,
            )
        else:
            # Execute pipeline synchronously with per-task events
            final_outputs = []
            all_success = True
            errors = []

            for stage_index, stage_task_ids in stage_task_map.items():
                # Notify stage change
                stage_agents = [t.agent_id for tid in stage_task_ids if (t := self._manager.get_task(tid)) is not None]
                if self._on_stage_change:
                    self._on_stage_change(stage_index + 1, total_stages, stage_agents)

                # Execute tasks in this stage
                for task_id in stage_task_ids:
                    task = self._manager.get_task(task_id)
                    if not task:
                        continue

                    # Skip if already terminal (shouldn't happen in fresh pipeline)
                    if task.status.is_terminal():
                        if task.result:
                            if task.result.success:
                                final_outputs.append(
                                    f"=== @{task.agent_id} ===\n{task.result.output}"
                                )
                            else:
                                all_success = False
                        continue

                    # Notify task started
                    if self._on_task_started:
                        self._on_task_started(task)

                    # Update status manager
                    self._status_running(task.agent_id, task.prompt[:40] if task.prompt else "")

                    try:
                        # Execute the task
                        result = await self._manager.execute_task(task_id)

                        # Update status based on result
                        if result.success:
                            self._status_completed(task.agent_id)
                        else:
                            self._status_failed(task.agent_id)
                    except asyncio.CancelledError:
                        self._status_failed(task.agent_id)
                        raise
                    finally:
                        self._status_idle(task.agent_id)

                    # Notify task complete
                    if self._on_task_complete:
                        self._on_task_complete(task, result)

                    # Emit intermediate output
                    if self._on_stage_output and result.success:
                        self._on_stage_output(task.agent_id, result.output)

                    # Collect output
                    if result.success:
                        final_outputs.append(f"=== @{task.agent_id} ===\n{result.output}")
                    else:
                        all_success = False
                        if task.status == TaskStatus.SKIPPED:
                            final_outputs.append(
                                f"=== @{task.agent_id} ===\n[Skipped: {result.error}]"
                            )
                        else:
                            errors.append(f"@{task.agent_id}: {result.error}")
                            final_outputs.append(
                                f"=== @{task.agent_id} ===\n[Failed: {result.error}]"
                            )

            # Signal pipeline completion to clear progress display
            if self._on_pipeline_complete:
                self._on_pipeline_complete()

            return ExecutionResult(
                success=all_success,
                output="\n\n".join(final_outputs),
                task_ids=all_task_ids,
                error="; ".join(errors) if errors else None,
            )

    async def _run_task_with_callback(self, task_id: str) -> None:
        """Run a task and call callbacks when starting/complete.

        Args:
            task_id: Task to run.
        """
        task = self._manager.get_task(task_id)
        agent_id = task.agent_id if task else None
        try:
            # Notify task started
            if self._on_task_started and task:
                self._on_task_started(task)

            if agent_id:
                self._status_running(agent_id, task.prompt[:40] if task and task.prompt else "")

            result = await self._manager.execute_task(task_id)

            if agent_id:
                if result.success:
                    self._status_completed(agent_id)
                else:
                    self._status_failed(agent_id)
        except asyncio.CancelledError:
            if agent_id:
                self._status_failed(agent_id)
            raise
        finally:
            if agent_id:
                self._status_idle(agent_id)
            if self._on_task_complete:
                task = self._manager.get_task(task_id)
                result = self._manager.get_result(task_id)
                self._on_task_complete(task, result)

    async def _run_pipeline_with_callback(
        self, task_ids: list[str], stage_task_map: dict[int, list[str]], total_stages: int
    ) -> None:
        """Run pipeline tasks and call callbacks when complete.

        Args:
            task_ids: All task IDs in pipeline.
            stage_task_map: Mapping of stage index to task IDs in that stage.
            total_stages: Total number of pipeline stages.
        """
        try:
            # Execute pipeline with per-task events (same pattern as sync pipeline)
            for stage_index, stage_task_ids in stage_task_map.items():
                # Notify stage change
                stage_agents = [t.agent_id for tid in stage_task_ids if (t := self._manager.get_task(tid)) is not None]
                if self._on_stage_change:
                    self._on_stage_change(stage_index + 1, total_stages, stage_agents)

                # Execute tasks in this stage
                for task_id in stage_task_ids:
                    task = self._manager.get_task(task_id)
                    if not task:
                        continue

                    # Skip if already terminal
                    if task.status.is_terminal():
                        continue

                    # Notify task started
                    if self._on_task_started:
                        self._on_task_started(task)

                    # Update status manager
                    self._status_running(task.agent_id, task.prompt[:40] if task.prompt else "")

                    try:
                        # Execute the task
                        result = await self._manager.execute_task(task_id)

                        # Update status based on result
                        if result.success:
                            self._status_completed(task.agent_id)
                        else:
                            self._status_failed(task.agent_id)
                    except asyncio.CancelledError:
                        self._status_failed(task.agent_id)
                        raise
                    finally:
                        self._status_idle(task.agent_id)

                    # Notify task complete
                    if self._on_task_complete:
                        self._on_task_complete(task, result)

                    # Emit intermediate output
                    if self._on_stage_output and result.success:
                        self._on_stage_output(task.agent_id, result.output)
        except Exception as e:
            # Log the exception to aid debugging
            logger.error("Pipeline execution failed with exception: %s", e, exc_info=True)
            # Ensure all tasks get completion callbacks even on error
            if self._on_task_complete:
                for task_id in task_ids:
                    task = self._manager.get_task(task_id)
                    result = self._manager.get_result(task_id)
                    if task and result:
                        self._on_task_complete(task, result)
            # Re-raise to avoid masking critical errors
            raise
        finally:
            # Signal pipeline completion to clear progress display
            if self._on_pipeline_complete:
                self._on_pipeline_complete()

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task identifier.

        Returns:
            Task if found.
        """
        return self._manager.get_task(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """List tasks, optionally filtered by status.

        Args:
            status: Filter by status.

        Returns:
            List of tasks.
        """
        return self._manager.list_tasks(status=status)

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task.

        Args:
            task_id: Task to cancel.

        Returns:
            True if cancelled.
        """
        # Also cancel the asyncio task if running
        if task_id in self._background_tasks:
            bg_task = self._background_tasks[task_id]
            if not bg_task.done():
                bg_task.cancel()

        return self._manager.cancel_task(task_id)
