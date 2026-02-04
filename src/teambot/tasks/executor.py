"""Task executor - bridges REPL commands to TaskManager."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field

from teambot.repl.parser import Command, CommandType
from teambot.tasks.manager import TaskManager
from teambot.tasks.models import Task, TaskStatus


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
    ):
        """Initialize executor.

        Args:
            sdk_client: Copilot SDK client for agent execution.
            max_concurrent: Maximum concurrent tasks.
            default_timeout: Default task timeout in seconds.
            on_task_complete: Callback when task completes (for notifications).
            on_task_started: Callback when task starts (for overlay updates).
            on_streaming_chunk: Callback for streaming chunks (agent_id, chunk).
        """
        self._sdk_client = sdk_client
        self._on_task_complete = on_task_complete
        self._on_task_started = on_task_started
        self._on_streaming_chunk = on_streaming_chunk

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

    async def _execute_agent_task(self, agent_id: str, prompt: str) -> str:
        """Execute a task via SDK.

        Args:
            agent_id: Agent to execute task.
            prompt: Task prompt (already includes persona context).

        Returns:
            Output from agent.
        """
        # Check if SDK client supports streaming
        if hasattr(self._sdk_client, "execute_streaming") and self._on_streaming_chunk:
            # Use streaming with callback
            def on_chunk(chunk: str):
                self._on_streaming_chunk(agent_id, chunk)

            return await self._sdk_client.execute_streaming(agent_id, prompt, on_chunk)
        else:
            # Fall back to regular execute
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
            result = await self._manager.execute_task(task.id)
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
            # Execute all in parallel and wait
            await asyncio.gather(
                *[self._manager.execute_task(t.id) for t in tasks],
                return_exceptions=True,
            )

            # Collect results
            outputs = []
            all_success = True
            errors = []

            for task in tasks:
                result = self._manager.get_result(task.id)
                if result:
                    if result.success:
                        outputs.append(f"=== @{task.agent_id} ===\n{result.output}")
                    else:
                        all_success = False
                        errors.append(f"@{task.agent_id}: {result.error}")
                        outputs.append(f"=== @{task.agent_id} ===\n[Failed: {result.error}]")

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
                )
                stage_task_ids.append(task.id)
                all_task_ids.append(task.id)

            previous_task_ids = stage_task_ids

        if command.background:
            # Start pipeline in background
            bg_task = asyncio.create_task(self._run_pipeline_with_callback(all_task_ids))
            for task_id in all_task_ids:
                self._background_tasks[task_id] = bg_task

            return ExecutionResult(
                success=True,
                output=f"Pipeline started in background ({len(command.pipeline)} stages)",
                task_ids=all_task_ids,
                background=True,
            )
        else:
            # Execute pipeline synchronously
            await self._manager.execute_all()

            # Get final output
            final_outputs = []
            all_success = True
            errors = []

            for task_id in all_task_ids:
                task = self._manager.get_task(task_id)
                result = self._manager.get_result(task_id)

                if result:
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
        try:
            # Notify task started
            if self._on_task_started:
                task = self._manager.get_task(task_id)
                if task:
                    self._on_task_started(task)

            await self._manager.execute_task(task_id)
        finally:
            if self._on_task_complete:
                task = self._manager.get_task(task_id)
                result = self._manager.get_result(task_id)
                self._on_task_complete(task, result)

    async def _run_pipeline_with_callback(self, task_ids: list[str]) -> None:
        """Run pipeline tasks and call callback when complete.

        Args:
            task_ids: All task IDs in pipeline.
        """
        try:
            await self._manager.execute_all()
        finally:
            if self._on_task_complete:
                for task_id in task_ids:
                    task = self._manager.get_task(task_id)
                    result = self._manager.get_result(task_id)
                    if task and result:
                        self._on_task_complete(task, result)

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
